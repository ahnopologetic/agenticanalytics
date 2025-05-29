import os
from pathlib import Path
import tempfile
import time
from typing import Optional

from git import Repo
import git
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import jwt
from pydantic import BaseModel
from supabase import Client, create_client
from google.adk.cli.fast_api import get_fast_api_app

from config import config
from structlog import get_logger

logger = get_logger()


# --- Config ---
supabase: Client = create_client(config.supabase_url, config.supabase_service_role_key)

# --- FastAPI app ---
AGENT_DIR = Path(__file__).parent
agent_app = get_fast_api_app(
    agent_dir=AGENT_DIR,
    allow_origins=["https://agenticanalytics.vercel.app", "http://localhost:5173"],
    web=True,
)
app = FastAPI()

app.mount("/agent", agent_app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agenticanalytics.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class GitHubTokenRequest(BaseModel):
    github_token: str


# --- Helpers ---
async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )
    access_token = authorization.split(" ", 1)[1]
    # Validate token with Supabase Auth API
    resp = supabase.auth.get_user(access_token)
    user = resp.user
    if not user or not user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase token."
        )
    return user.id


# --- Endpoints ---
@app.post("/github/token")
async def save_github_token(
    body: GitHubTokenRequest, user_id: str = Depends(get_current_user_id)
):
    # Upsert the user's GitHub token
    data = {"user_id": user_id, "github_token": body.github_token}
    result = (
        supabase.table("user_github_tokens")
        .upsert(data, on_conflict="user_id")
        .execute()
    )
    logger.info("GitHub token saved", result=result)
    return {"success": True}


@app.get("/github/repos")
async def get_github_repos(user_id: str = Depends(get_current_user_id)):
    # Fetch the user's GitHub token from Supabase
    result = (
        supabase.table("user_github_tokens")
        .select("github_token")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    github_token = result.data.get("github_token")
    logger.info("GitHub token", github_token=github_token)
    if github_token is None:
        raise HTTPException(status_code=404, detail="GitHub token not found for user.")

    async with httpx.AsyncClient() as client:
        gh_resp = await client.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github+json",
            },
        )
    if gh_resp.status_code != 200:
        raise HTTPException(
            status_code=gh_resp.status_code, detail="Failed to fetch GitHub repos."
        )
    return JSONResponse(content=gh_resp.json())


class CloneRepoRequest(BaseModel):
    repo_name: str


@app.post("/github/clone-repo")
async def clone_github_repo(
    request: CloneRepoRequest,
    user_id: str = Depends(get_current_user_id),
    repo_path: str | Path = Path("/tmp/agentic-analytics"),
):
    # Fetch the user's GitHub token from Supabase
    result = (
        supabase.table("user_github_tokens")
        .select("github_token")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    github_token = result.data.get("github_token")
    if github_token is None:
        logger.error("GitHub token not found for user.", user_id=user_id)
        raise HTTPException(status_code=404, detail="GitHub token not found for user.")

    now = int(time.time())
    jwt_payload = {"iat": now - 60, "exp": now + 600, "iss": config.github_app_id}
    signed_jwt = jwt.encode(
        jwt_payload, config.github_app_private_key, algorithm="RS256"
    )

    async with httpx.AsyncClient() as client:
        # First get the installation ID for this repository
        installations_resp = await client.get(
            "https://api.github.com/app/installations",
            headers={
                "Authorization": f"Bearer {signed_jwt}",
                "Accept": "application/vnd.github+json",
            },
        )

        if installations_resp.status_code != 200:
            logger.error(
                "Failed to fetch GitHub app installations",
                installations_resp=installations_resp,
                installations_resp_json=installations_resp.json(),
            )
            raise HTTPException(
                status_code=installations_resp.status_code,
                detail="Failed to fetch GitHub app installations",
            )

        installations = installations_resp.json()
        if not installations:
            raise HTTPException(
                status_code=404, detail="No GitHub app installations found"
            )

        installation_id = installations[0]["id"]

        # Exchange JWT for installation access token
        token_resp = await client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {signed_jwt}",
                "Accept": "application/vnd.github+json",
            },
        )

        if token_resp.status_code != 201:
            logger.error(
                "Failed to get installation access token",
                token_resp=token_resp,
                token_resp_json=token_resp.json(),
            )
            raise HTTPException(
                status_code=token_resp.status_code,
                detail="Failed to get installation access token",
            )

        installation_token = token_resp.json()["token"]

    # Create a temporary directory for the clone
    temp_dir = tempfile.mkdtemp()

    # Construct the repo URL with token for auth
    repo_url = f"https://x-access-token:{installation_token}@github.com/{request.repo_name}.git"

    try:
        # Clone the repository
        repo = Repo.clone_from(repo_url, temp_dir)
        repo_path = repo.working_dir
    except git.GitCommandError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clone repository: {str(e)}"
        )

    logger.info("Cloned repository", repo_path=repo_path)

    return repo_path
