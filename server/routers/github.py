from pathlib import Path
from typing import List

import httpx
from config import config
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    all_repos = []
    page = 1
    async with httpx.AsyncClient() as client:
        while True:
            gh_resp = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github+json",
                },
                params={
                    "visibility": "all",
                    "affiliation": "owner,collaborator,organization_member",
                    "per_page": 100,
                    "page": page,
                },
            )
            if gh_resp.status_code != 200:
                raise HTTPException(
                    status_code=gh_resp.status_code,
                    detail="Failed to fetch GitHub repos.",
                )
            data = gh_resp.json()
            if not data:
                break
            all_repos.extend(data)
            if len(data) < 100:
                break
            page += 1
    return all_repos


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


@router.get("/info")
async def get_github_repo_info(
    repo: str = Query(..., description="Full repo name, e.g. 'owner/repo'"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile or not getattr(profile, "github_token", None):
        raise HTTPException(status_code=404, detail="GitHub token not found for user.")
    github_token = profile.github_token
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient() as client:
        # Get latest commit
        commits_url = f"https://api.github.com/repos/{repo}/commits"
        commits_resp = await client.get(commits_url, headers=headers)
        if commits_resp.status_code != 200:
            logger.error(
                "Failed to fetch commits.",
                status_code=commits_resp.status_code,
                commits_resp=commits_resp.json(),
            )
            raise HTTPException(
                status_code=commits_resp.status_code, detail="Failed to fetch commits."
            )
        commits = commits_resp.json()
        if not commits:
            raise HTTPException(
                status_code=404, detail="No commits found for this repo."
            )
        latest_commit = commits[0]
        sha = latest_commit.get("sha")
        commit_message = latest_commit.get("commit", {}).get("message", "")
        author = latest_commit.get("commit", {}).get("author", {}).get("name", "")
        date = latest_commit.get("commit", {}).get("author", {}).get("date", "")
        # Get status for latest commit
        status_url = f"https://api.github.com/repos/{repo}/commits/{sha}/status"
        status_resp = await client.get(status_url, headers=headers)
        status = None
        if status_resp.status_code == 200:
            status_json = status_resp.json()
            status = status_json.get("state")  # 'success', 'failure', 'pending', etc.
        return {
            "sha": sha,
            "message": commit_message,
            "author": author,
            "date": date,
            "status": status,
        }
