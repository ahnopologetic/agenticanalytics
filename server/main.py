from pathlib import Path
from typing import List, Optional

import httpx
from config import config
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app
from pydantic import BaseModel
from structlog import get_logger
from supabase import Client, create_client
from utils.github import aclone_repository

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


class MixReposRequest(BaseModel):
    repo_names: List[str]


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

    return await aclone_repository(request.repo_name)

