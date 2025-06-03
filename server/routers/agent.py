from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Any, Optional
from structlog import get_logger
from agents.runner import repo_reader_task_manager
from .deps import get_current_user
from gotrue.types import User

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
    from fastapi import Header
    from supabase import Client, create_client
    from config import config

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
async def get_sessions(user: User = Depends(get_current_user)):
    sessions = await repo_reader_task_manager.list_sessions(user_id=user.id)
    return sessions.model_dump(exclude_none=True)


@router.get("/sessions/session")
async def get_session(
    session_id: str = Query(..., description="The session ID"),
    user: User = Depends(get_current_user),
):
    return await repo_reader_task_manager.get_session(
        session_id=session_id, user_id=user.id
    )


@router.post("/run")
async def run(
    request: AgentRequest,
    user: User = Depends(get_current_user),
) -> AgentResponse:
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


@router.post("/create-task")
async def create_task(
    request: AgentRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
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
            "user_id": user.id,
        }
    except Exception as e:
        logger.error("Error creating task", error=e)
        return AgentResponse(
            message="Error creating task",
            status="error",
            data={},
            session_id=request.session_id,
            user_id=user.id,
        )
    return response
