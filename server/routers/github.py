from pathlib import Path
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
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


class GithubRepo(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    owner: dict
    html_url: str
    description: str | None = None
    language: str | None = None
    stargazers_count: int = 0
    watchers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    default_branch: str = "main"
    visibility: str = "public"


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


@router.get("/repos", response_model=list[GithubRepo])
async def get_github_repos(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[GithubRepo]:
    """
    Fetch all user and org repositories (including private) for the authenticated user.
    """
    profile = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile or not getattr(profile, "github_token", None):
        raise HTTPException(status_code=404, detail="GitHub token not found for user.")
    github_token = profile.github_token
    logger.info("GitHub token", github_token=github_token)
    all_repos = []

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient() as client:
        # Fetch user repos (all, including private)
        page = 1
        while True:
            user_repos_resp = await client.get(
                "https://api.github.com/user/repos",
                headers=headers,
                params={
                    "visibility": "all",
                    "affiliation": "owner,collaborator,organization_member",
                    "per_page": 100,
                    "page": page,
                },
            )
            if user_repos_resp.status_code != 200:
                raise HTTPException(
                    status_code=user_repos_resp.status_code,
                    detail="Failed to fetch GitHub user repos.",
                )
            data = user_repos_resp.json()
            if not data:
                break
            all_repos.extend(data)
            if len(data) < 100:
                break
            page += 1

        # Fetch orgs for the user
        orgs_resp = await client.get(
            "https://api.github.com/user/orgs",
            headers=headers,
        )
        if orgs_resp.status_code == 200:
            orgs = orgs_resp.json()
        else:
            orgs = []

        # For each org, fetch all repos (including private)
        for org in orgs:
            org_login = org.get("login")
            if not org_login:
                continue
            page = 1
            while True:
                org_repos_resp = await client.get(
                    f"https://api.github.com/orgs/{org_login}/repos",
                    headers=headers,
                    params={
                        "type": "all",  # includes private and public
                        "per_page": 100,
                        "page": page,
                    },
                )
                if org_repos_resp.status_code != 200:
                    logger.warning(
                        "Failed to fetch org repos",
                        org=org_login,
                        status_code=org_repos_resp.status_code,
                        detail=org_repos_resp.text,
                    )
                    break
                org_data = org_repos_resp.json()
                if not org_data:
                    break
                all_repos.extend(org_data)
                if len(org_data) < 100:
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
    # github_token = profile.github_token
    # TODO: Implement cloning logic
    return {"success": True, "repo": request.repo_name}


@router.get("/info")
async def get_github_repo_info(
    repo: str = Query(..., description="Full repo name, e.g. 'owner/repo'"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # sanitize repo name
    repo = repo.strip()
    if repo.startswith("https://github.com/"):
        repo = repo.split("https://github.com/")[1]
    if repo.endswith(".git"):
        repo = repo.split(".git")[0]
    if "/" not in repo:
        raise HTTPException(status_code=400, detail="Invalid repo name.")

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
