from typing import Any, Optional

from agents.runner import (
    MainAgentTaskManager,
    get_agentic_analytics_task_manager,
)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from db_models import Repo
from google.adk.sessions.session import Session
from gotrue.types import User
from pydantic import BaseModel, Field
from structlog import get_logger
from utils.db_session import get_db
from utils.github import aclone_repo

from .deps import get_current_user

logger = get_logger()

router = APIRouter()


# --- Models ---
class AgentRequest(BaseModel):
    message: str = Field(..., description="The message to process")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context for the request"
    )
    session_id: Optional[str] = Field(
        None, description="Session identifier for stateful interactions"
    )


class AgentResponse(BaseModel):
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


# --- Dependency ---
async def get_current_user_id(
    authorization: Optional[str] = Depends(lambda: None),
) -> str:
    from config import config
    from supabase import Client, create_client

    supabase: Client = create_client(
        config.supabase_url, config.supabase_service_role_key
    )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )
    access_token = authorization.split(" ", 1)[1]
    resp = supabase.auth.get_user(access_token)
    user = resp.user
    if not user or not user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase token."
        )
    return user.id


# --- Endpoints ---
@router.get("/sessions")
async def get_sessions(
    user: User = Depends(get_current_user),
    agentic_analytics_task_manager: MainAgentTaskManager = Depends(
        get_agentic_analytics_task_manager
    ),
):
    sessions = await agentic_analytics_task_manager.list_sessions(user_id=user.id)
    return sessions.model_dump(exclude_none=True)


@router.get("/sessions/session")
async def get_session(
    session_id: str = Query(..., description="The session ID"),
    user: User = Depends(get_current_user),
    agentic_analytics_task_manager: MainAgentTaskManager = Depends(
        get_agentic_analytics_task_manager
    ),
):
    return await agentic_analytics_task_manager.get_session(
        session_id=session_id, user_id=user.id
    )


@router.post("/session")
async def create_session(
    user: User = Depends(get_current_user),
    agentic_analytics_task_manager: MainAgentTaskManager = Depends(
        get_agentic_analytics_task_manager
    ),
) -> Session:
    return await agentic_analytics_task_manager.create_session(
        context={"user_id": user.id}, session_id=None
    )


@router.post("/run")
async def run(
    request: AgentRequest,
    user: User = Depends(get_current_user),
    agentic_analytics_task_manager: MainAgentTaskManager = Depends(
        get_agentic_analytics_task_manager
    ),
) -> AgentResponse:
    try:
        response = await agentic_analytics_task_manager.execute(
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


@router.post("/create-task")
async def create_task(
    body: AgentRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from agents.runner import agentic_analytics_task_manager

    repo_name = body.message  # TODO: structure the request message
    repo_path = await aclone_repo(repo_name)

    context = {
        **body.context,
        "repo_path": repo_path,
        "repo_name": repo_name,
    }
    session = await agentic_analytics_task_manager.create_session(
        context=context, session_id=body.session_id
    )
    repo = (
        db.query(Repo).filter(Repo.name == repo_name, Repo.user_id == user.id).first()
    )
    if not repo:
        repo = Repo(
            name=repo_name,
            user_id=user.id,
            url=f"https://github.com/{repo_name}",
            session_id=session.id,
        )
        db.add(repo)
        db.commit()
    else:
        repo.url = f"https://github.com/{repo_name}"
        repo.session_id = session.id
        db.commit()

    context["repo_id"] = repo.id

    try:
        background_tasks.add_task(
            agentic_analytics_task_manager.execute,
            repo_path,
            context,
            body.session_id or session.id,
        )
        response = {
            "status": "success",
            "message": "Task created successfully",
            "data": {},
            "session_id": body.session_id,
            "user_id": user.id,
        }
    except Exception as e:
        logger.error("Error creating task", error=e)
        return AgentResponse(
            message="Error creating task",
            status="error",
            data={},
            session_id=body.session_id,
            user_id=user.id,
        )
    return response
