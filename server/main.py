import os
from pathlib import Path
from typing import Any, List, Optional

import httpx
from config import config
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app
from pydantic import BaseModel, Field
from structlog import get_logger
from supabase import Client, create_client
from utils.github import aclone_repository
from repo_reader.runner import repo_reader_task_manager

logger = get_logger()


# --- Config ---
supabase: Client = create_client(config.supabase_url, config.supabase_service_role_key)

# --- FastAPI app ---
# AGENT_DIR = Path(__file__).parent
AGENT_DIR = os.path.abspath(os.path.dirname(__file__))
# agent_app = get_fast_api_app(
#     agent_dir=AGENT_DIR,
#     allow_origins=["https://agenticanalytics.vercel.app", "http://localhost:5173"],
#     web=True,
# )
# app = get_fast_api_app(
#     agent_dir=AGENT_DIR,
#     allow_origins=["*"],
#     web=True,
# )
app = FastAPI(root_path="/")

# app.mount("/agent", agent_app)
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


@app.get("/agent/sessions")
async def get_sessions(user_id: str = Depends(get_current_user_id)):
    sessions = await repo_reader_task_manager.session_service.list_sessions(
        app_name="repo-reader", user_id=user_id
    )
    return JSONResponse(content=sessions.model_dump(exclude_none=True))


@app.get("/agent/sessions/{session_id}")
async def get_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    session = await repo_reader_task_manager.session_service.get_session(
        app_name="repo-reader", user_id=user_id, session_id=session_id
    )
    return JSONResponse(content=session.model_dump(exclude_none=True))


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
