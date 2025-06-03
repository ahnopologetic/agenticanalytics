from pathlib import Path
from typing import List

import httpx
from config import config
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from structlog import get_logger
from supabase import Client, create_client
from utils.github import aclone_repository
from .deps import get_current_user
from gotrue.types import User

logger = get_logger()
supabase: Client = create_client(config.supabase_url, config.supabase_service_role_key)

router = APIRouter()


# --- Models ---
class GitHubTokenRequest(BaseModel):
    github_token: str


class CloneRepoRequest(BaseModel):
    repo_name: str


class MixReposRequest(BaseModel):
    repo_names: List[str]


# --- Endpoints ---
@router.post("/token")
async def save_github_token(
    body: GitHubTokenRequest, user: User = Depends(get_current_user)
):
    data = {"user_id": user.id, "github_token": body.github_token}
    result = (
        supabase.table("user_github_tokens")
        .upsert(data, on_conflict="user_id")
        .execute()
    )
    logger.info("GitHub token saved", result=result)
    return {"success": True}


@router.get("/repos")
async def get_github_repos(user: User = Depends(get_current_user)):
    result = (
        supabase.table("user_github_tokens")
        .select("github_token")
        .eq("user_id", user.id)
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
    return gh_resp.json()


@router.post("/clone-repo")
async def clone_github_repo(
    request: CloneRepoRequest,
    user: User = Depends(get_current_user),
    repo_path: str | Path = Path("/tmp/agentic-analytics"),
):
    result = (
        supabase.table("user_github_tokens")
        .select("github_token")
        .eq("user_id", user.id)
        .single()
        .execute()
    )
    github_token = result.data.get("github_token")
    if github_token is None:
        logger.error("GitHub token not found for user.", user_id=user.id)
        raise HTTPException(status_code=404, detail="GitHub token not found for user.")
    return await aclone_repository(request.repo_name)
