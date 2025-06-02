import os
import os
from pathlib import Path
from typing import Any, List, Optional
from typing import Any, List, Optional

import httpx
from config import config
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    status,
    Request,
    Response,
    Cookie,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from google.adk.cli.fast_api import get_fast_api_app
from pydantic import BaseModel, Field
from pydantic import BaseModel, Field
from structlog import get_logger
from supabase import Client, create_client
from utils.github import aclone_repository
from agents.runner import repo_reader_task_manager
import secrets
import base64
from cryptography.fernet import Fernet
import uuid

logger = get_logger()


supabase: Client = create_client(config.supabase_url, config.supabase_service_role_key)

app = FastAPI(root_path="/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agenticanalytics.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GitHubTokenRequest(BaseModel):
    github_token: str


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


class AgentRequest(BaseModel):
    """Standard A2A agent request format."""

    message: str = Field(..., description="The message to process")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context for the request"
    )
    session_id: Optional[str] = Field(
        None, description="Session identifier for stateful interactions"
    )


class AgentResponse(BaseModel):
    """Standard A2A agent response format."""

    message: str = Field(..., description="The response message")
    status: str = Field(
        default="success", description="Status of the response (success, error)"
    )
    data: dict[str, Any] = Field(
        default_factory=dict, description="Additional data returned by the agent"
    )
    session_id: Optional[str] = Field(
        None, description="Session identifier for stateful interactions"
    )


DEFAULT_APP_NAME = "repo_reader"


@app.get("/agent/sessions")
async def get_sessions(user_id: str = Depends(get_current_user_id)):
    sessions = await repo_reader_task_manager.list_sessions(user_id=user_id)
    return JSONResponse(content=sessions.model_dump(exclude_none=True))


@app.get("/agent/sessions/session")
async def get_session(
    session_id: str = Query(
        ..., description="The session ID"
    ),  # because session id shaped like this: owner/repo_name
    user_id: str = Depends(get_current_user_id),
):
    return await repo_reader_task_manager.get_session(
        session_id=session_id, user_id=user_id
    )


@app.post("/agent/run")
async def run(request: AgentRequest) -> AgentResponse:
    try:
        response = await repo_reader_task_manager.execute(
            request.message, request.context, request.session_id
        )
    except Exception as e:
        logger.error("Error running agent", error=e)
        return AgentResponse(
            message="Error running agent",
            status="error",
            data={},
            session_id=request.session_id,
        )

    logger.info("Agent response", response=response)
    return AgentResponse(
        message=response["message"],
        status=response["status"],
        data=response["data"],
        session_id=response["session_id"],
    )


@app.post("/agent/create-task")
async def create_task(request: AgentRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(
            repo_reader_task_manager.execute,
            request.message,
            request.context,
            request.session_id,
        )
        response = {
            "status": "success",
            "message": "Task created successfully",
            "data": {},
            "session_id": request.session_id,
        }
    except Exception as e:
        logger.error("Error creating task", error=e)
        return AgentResponse(
            message="Error creating task",
            status="error",
            data={},
            session_id=request.session_id,
        )
    return JSONResponse(content=response)


# --- GitHub OAuth2 ---
GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_USER_URL = "https://api.github.com/user"
GITHUB_API_ORGS_URL = "https://api.github.com/user/orgs"
FERNET_SECRET = config.fernet_secret
fernet = Fernet(FERNET_SECRET)

OAUTH_STATE_COOKIE = "gh_oauth_state"
OAUTH_TOKEN_COOKIE = "gh_oauth_token"

# Temporary in-memory session store for OAuth (for dev)
github_oauth_sessions = {}

FRONTEND_URL = config.frontend_base_url

@app.get("/auth/github/login")
async def github_oauth_login(response: Response):
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": config.github_oauth_client_id,
        "scope": "read:org",
        "redirect_uri": f"{config.base_url}/auth/github/callback",
        "state": state,
        "allow_signup": "false",
    }
    from urllib.parse import urlencode
    url = f"{GITHUB_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    response.set_cookie(OAUTH_STATE_COOKIE, state, httponly=True, secure=True, max_age=600)
    return Response(status_code=307, headers={"Location": url})

@app.get("/auth/github/callback")
async def github_oauth_callback(request: Request, response: Response, code: str, state: str):
    # # Validate state
    # if not gh_oauth_state or gh_oauth_state != state:
    #     raise HTTPException(status_code=400, detail="Invalid OAuth state.")
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_OAUTH_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": config.github_oauth_client_id,
                "client_secret": config.github_oauth_client_secret,
                "code": code,
                "redirect_uri": f"{config.base_url}/auth/github/callback",
                "state": state,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            logger.error("GitHub OAuth callback", token_resp=token_resp.json())
            raise HTTPException(status_code=400, detail="Failed to obtain GitHub access token.")
        # Get user info
        user_resp = await client.get(GITHUB_API_USER_URL, headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"})
        user_data = user_resp.json()
        github_login = user_data.get("login")
        if not github_login:
            raise HTTPException(status_code=400, detail="Failed to get GitHub user info.")
        # Get orgs
        orgs_resp = await client.get(GITHUB_API_ORGS_URL, headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"})
        orgs = orgs_resp.json() if orgs_resp.status_code == 200 else []
    # Store encrypted token and github_login in Supabase
    user_id = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            supa_token = auth_header.split(" ", 1)[1]
            resp = supabase.auth.get_user(supa_token)
            user = resp.user
            if user and user.id:
                user_id = user.id
    except Exception:
        pass
    encrypted_token = fernet.encrypt(access_token.encode()).decode()
    if user_id:
        data = {"user_id": user_id, "github_token": encrypted_token, "github_login": github_login}
        supabase.table("user_github_tokens").upsert(data, on_conflict="user_id").execute()
    # Store orgs, github_login, and encrypted_token in a temporary session
    session_id = str(uuid.uuid4())
    github_oauth_sessions[session_id] = {"orgs": orgs, "github_login": github_login, "encrypted_token": encrypted_token}
    # Redirect to frontend with session_id
    redirect_url = f"{FRONTEND_URL}/github-connect?session_id={session_id}"
    return RedirectResponse(url=redirect_url, status_code=302)

@app.get("/auth/github/orgs")
async def github_oauth_orgs(session_id: str):
    session = github_oauth_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return session

@app.get("/auth/github/repos")
async def github_oauth_repos(session_id: str):
    session = github_oauth_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    # Get encrypted token from session (store it in session on callback)
    encrypted_token = session.get("encrypted_token")
    if not encrypted_token:
        raise HTTPException(status_code=400, detail="No access token in session.")
    access_token = fernet.decrypt(encrypted_token.encode()).decode()
    async with httpx.AsyncClient() as client:
        # Get user info
        user_resp = await client.get(GITHUB_API_USER_URL, headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"})
        user = user_resp.json()
        # Get orgs
        orgs_resp = await client.get(GITHUB_API_ORGS_URL, headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"})
        orgs = orgs_resp.json() if orgs_resp.status_code == 200 else []
        # Get user repos
        user_repos_resp = await client.get("https://api.github.com/user/repos?per_page=100", headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"})
        user_repos = user_repos_resp.json() if user_repos_resp.status_code == 200 else []
        owners = [{
            "type": "user",
            "login": user.get("login"),
            "avatar_url": user.get("avatar_url"),
            "repos": user_repos,
        }]
        # Get org repos for each org
        for org in orgs:
            org_login = org.get("login")
            org_avatar = org.get("avatar_url")
            org_repos_resp = await client.get(f"https://api.github.com/orgs/{org_login}/repos?per_page=100", headers={"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"})
            org_repos = org_repos_resp.json() if org_repos_resp.status_code == 200 else []
            owners.append({
                "type": "org",
                "login": org_login,
                "avatar_url": org_avatar,
                "repos": org_repos,
            })
    return {"owners": owners}
