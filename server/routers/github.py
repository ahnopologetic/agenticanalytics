from pathlib import Path
from typing import List

import httpx
from config import config
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from structlog import get_logger
from sqlalchemy.orm import Session
from utils.db_session import get_db
from db_models import Profile
from .deps import get_current_user
from gotrue.types import User

logger = get_logger()

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
    body: GitHubTokenRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    profile.github_token = body.github_token  # Add this field to Profile if not present
    db.add(profile)
    db.commit()
    logger.info("GitHub token saved", user_id=user.id)
    return {"success": True}


@router.get("/repos")
async def get_github_repos(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile or not getattr(profile, "github_token", None):
        raise HTTPException(status_code=404, detail="GitHub token not found for user.")
    github_token = profile.github_token
    logger.info("GitHub token", github_token=github_token)
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
    db: Session = Depends(get_db),
    repo_path: str | Path = Path("/tmp/agentic-analytics"),
):
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile or not getattr(profile, "github_token", None):
        logger.error("GitHub token not found for user.", user_id=user.id)
        raise HTTPException(status_code=404, detail="GitHub token not found for user.")
    github_token = profile.github_token
    # TODO: Implement cloning logic
    return {"success": True, "repo": request.repo_name}
