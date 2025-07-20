import tempfile
import time
from typing import Optional

import git
import httpx
import jwt
from config import config
from fastapi import HTTPException
from git import Repo
from google.adk.tools import ToolContext
from structlog import get_logger

logger = get_logger()


async def get_installation_token() -> str:
    """Get GitHub installation access token."""
    now = int(time.time())
    jwt_payload = {"iat": now - 60, "exp": now + 600, "iss": config.github_app_id}
    signed_jwt = jwt.encode(
        jwt_payload, config.github_app_private_key, algorithm="RS256"
    )

    async with httpx.AsyncClient() as client:
        # Get installation ID
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

        # Get installation access token
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

        return token_resp.json()["token"]


async def get_remote_default_branch(repo_url: str) -> Optional[str]:
    """
    Attempts to determine the default branch of a remote Git repository.

    Args:
        repo_url (str): The URL of the remote Git repository.

    Returns:
        str or None: The name of the default branch, or None if it cannot be determined.
    """
    try:
        result = Repo.git.ls_remote("--symref", repo_url, "HEAD")

        lines = result.splitlines()
        for line in lines:
            if "HEAD" in line and "refs/heads/" in line:
                branch_name = line.split("refs/heads/")[-1].split("HEAD")[0].strip()
                return branch_name
        return None

    except Exception as e:
        logger.error("Error getting remote default branch", error=e)
        return None


async def aclone_repository(
    tool_context: ToolContext, repo_name: str, branch: Optional[str] = None
) -> str:
    """
    Clone a GitHub repository and return the path to the cloned repository.

    Args:
        repo_name: str - the name of the repository to clone (e.g. "facebook/react", "facebook/react-native")
        branch: str | None - the name of the branch to clone (defaults to repository's default branch)

    Returns:
        str - the path to the cloned repository

    Raises:
        HTTPException - if the repository cannot be cloned

    """
    parts = repo_name.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise HTTPException(
            status_code=400,
            detail="Repository name must be in the format of 'owner/repo'",
        )

    if not branch:
        default_branch = await get_remote_default_branch(
            f"https://github.com/{repo_name}.git"
        )
        logger.debug("Default branch", default_branch=default_branch)
        branch = default_branch

    installation_token = await get_installation_token()
    logger.debug("Installation token", installation_token=installation_token)
    temp_dir = tempfile.mkdtemp()

    repo_url = f"https://x-access-token:{installation_token}@github.com/{repo_name}.git"

    try:
        # Clone the repository with specific branch if provided, otherwise use default branch
        if branch:
            repo = Repo.clone_from(repo_url, temp_dir, branch=branch)
        else:
            repo = Repo.clone_from(repo_url, temp_dir)
        repo_path = repo.working_dir
    except git.GitCommandError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clone repository: {str(e)}"
        )

    logger.info("Cloned repository", repo_path=repo_path, branch=branch or "default")
    tool_context.state["git_repository_path"] = repo_path
    tool_context.state["status"] = "cloned"
    return repo_path


async def apull_repository(repo_path: str) -> str:
    """
    Pull the repository and return the path to the pulled repository.
    """
    try:
        repo = Repo(repo_path)
        repo.pull()
    except git.GitCommandError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to pull repository: {str(e)}"
        )

    logger.info("Pulled repository", repo_path=repo_path)
    return repo_path


async def aswitch_branch(repo_path: str, branch: str) -> str:
    """
    Switch the branch of the repository and return the path to the repository.
    """
    try:
        repo = Repo(repo_path)
        repo.git.checkout(branch)
    except git.GitCommandError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to switch branch: {str(e)}"
        )

    logger.info("Switched branch", repo_path=repo_path, branch=branch)
    return repo_path
