import asyncio
import tempfile
import time

import git
import httpx
import jwt
from config import config
from fastapi import HTTPException
from git import Repo
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


async def aclone_repository(repo_name: str, branch: str = "main") -> str:
    """
    Clone a GitHub repository and return the path to the cloned repository.

    Args:
        repo_name: str - the name of the repository to clone (e.g. "facebook/react", "facebook/react-native")
        branch: str - the name of the branch to clone (defaults to "main")

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

    installation_token = await get_installation_token()
    # Create a temporary directory for the clone
    temp_dir = tempfile.mkdtemp()

    # Construct the repo URL with token for auth
    repo_url = f"https://x-access-token:{installation_token}@github.com/{repo_name}.git"

    try:
        # Clone the repository with specific branch
        repo = Repo.clone_from(repo_url, temp_dir, branch=branch)
        repo_path = repo.working_dir
    except git.GitCommandError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clone repository: {str(e)}"
        )

    logger.info("Cloned repository", repo_path=repo_path, branch=branch)
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
