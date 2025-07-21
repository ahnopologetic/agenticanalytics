import asyncio  # For async operations and delays
from pathlib import Path
from typing import Optional

import structlog
from db_models import Repo
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from utils.db_session import get_db
from utils.github import (
    aclone_repository,
)  # Assuming aclone_repository can raise specific exceptions

logger = structlog.get_logger(__name__)


def save_repo_to_db(
    tool_context: ToolContext,
    repo_name: str,
    branch: Optional[
        str
    ] = None,  # Make branch optional for consistency with aclone_repository
) -> dict:
    """
    Save the repository to the database.
    Args:
        tool_context: ToolContext
        repo_name: str
        branch: Optional[str] - the branch to clone the repository
    Returns:
        dict:
            {
                "status": "success",
                "repo_id": str(repo.id),
            }
    """
    db_session = next(get_db())

    # check if repo already exists
    repo = (
        db_session.query(Repo)
        .filter(Repo.url == f"https://github.com/{repo_name}")
        .first()
    )
    if repo:
        repo.session_id = tool_context.state.get("session_id", "")
        logger.debug("Repo already exists", repo=repo)
        logger.debug(
            "Repo session is updated",
            session_id=tool_context.state.get("session_id", ""),
        )
        tool_context.state["repo_id"] = str(repo.id)
        db_session.commit()
        return {"status": "success", "repo_id": str(repo.id)}

    try:
        repo = Repo(
            name=repo_name,
            user_id=tool_context.state["user_id"],
            url=f"https://github.com/{repo_name}",
            label=repo_name,
            description=f"Repository {repo_name} cloned from {branch if branch else 'default'} branch",  # Adjust description
            session_id=tool_context.state.get("session_id", ""),
        )
        db_session.add(repo)
        db_session.commit()
        tool_context.state["repo_id"] = str(repo.id)
    except Exception as e:
        logger.error(f"Error saving repository to database: {e}")
        raise e
    finally:
        db_session.close()

    return {"status": "success", "repo_id": str(repo.id)}


# --- New Wrapper Tool for aclone_repository with Retry Logic ---
async def aclone_repository_with_retry(
    tool_context: ToolContext,
    repo_name: str,
    branch: Optional[str] = None,  # Initial branch, can be None
) -> dict:
    """
    Attempts to clone a repository, retrying with common alternative branches
    if the initial attempt fails due to a branch not found error.

    Args:
        tool_context: ToolContext
        repo_name: str
        branch: Optional[str]
    Returns:
        dict:
            {
                "status": "success",
                "cloned_branch": str,
                "path": str,
            }
    """
    # Define common alternative branches to try
    alternative_branches = ["main", "master", "develop"]
    # Remove the initial branch from alternatives if it's in the list
    if branch in alternative_branches:
        alternative_branches.remove(branch)

    # Prioritize the explicitly provided branch if it exists
    branches_to_try = [branch] if branch else []
    branches_to_try.extend(alternative_branches)

    # Ensure no duplicates and keep order
    branches_to_try_unique = []
    seen = set()
    for b in branches_to_try:
        if b and b not in seen:  # Ensure branch is not None or empty
            branches_to_try_unique.append(b)
            seen.add(b)

    logger.info(
        f"Attempting to clone {repo_name} with branches: {branches_to_try_unique}"
    )

    for current_branch in branches_to_try_unique:
        try:
            logger.info(f"Trying to clone {repo_name} using branch: {current_branch}")
            # Assuming aclone_repository is an async function
            result = await aclone_repository(
                tool_context=tool_context,
                repo_name=repo_name,
                branch=current_branch,
            )

        except Exception as e:
            is_branch_not_found_error = False
            if (
                f"branch {current_branch} not found" in str(e).lower()
                or "reference not found" in str(e).lower()
            ):
                is_branch_not_found_error = True

            if (
                is_branch_not_found_error
                and current_branch != branches_to_try_unique[-1]
            ):
                logger.warning(
                    f"Failed to clone {repo_name} with branch '{current_branch}' (Branch not found). "
                    f"Attempting next branch. Error: {e}"
                )
                await asyncio.sleep(1)  # Small delay before next attempt
            else:
                logger.error(
                    f"Failed to clone {repo_name} after all attempts or due to unhandled error: {e}"
                )
                return {
                    "status": "error",
                    "error": str(e),
                }

        logger.info(
            f"Successfully cloned {repo_name} with branch: {current_branch}"
        )
        if Path(result).exists():
            break

    return {
        "status": "success",
        "cloned_branch": current_branch,
        "path": tool_context.state["git_repository_path"],
    }


git_manager_agent = LlmAgent(
    name="git_manager_agent",
    model="gemini-2.5-flash",
    description="Manage the git repository.",
    instruction="""
    Given the repository url, first save the repository to the database and then clone the repository.
    If the user input is a branch, then use the branch name to clone the repository.

    **Important:** When cloning the repository, use the `aclone_repository_with_retry` tool. This tool
    will intelligently attempt to clone, trying common alternative branches like 'main' or 'master'
    if the initial attempt or inferred branch fails.

    <example>
    Case 1:
        User Input: https://github.com/UnlyEd/next-right-now/tree/main

        Tool Calls:
            1. Function Call: aclone_repository_with_retry(repo_name="UnlyEd/next-right-now", branch="main")
            Reason: The repository name is the part of the URL that identifies the repository. From the given URL, the repository name is "UnlyEd/next-right-now". This tool handles retries with alternative branches.
            2. Function Call: save_repo_to_db(repo_name="UnlyEd/next-right-now", branch="main")
            Reason: Save the repository to the database after cloning.
        Output:
            {
                "repo_id": "1234567890",
                "cloned_branch": "main",
                "path": "/tmp/some-repo-path",
                "status": "success",
            }

    Case 2:
        User Input: https://github.com/facebook/react

        Tool Calls:
            1. Function Call: aclone_repository_with_retry(repo_name="facebook/react")
            Reason: The repository name is the part of the URL that identifies the repository. From the given URL, the repository name is "facebook/react". This tool handles retries with alternative branches.
            2. Function Call: save_repo_to_db(repo_name="facebook/react")
            Reason: Save the repository to the database after cloning.
        Output:
            {
                "repo_id": "123",
                "cloned_branch": "master",
                "path": "/tmp/some-repo-path",
                "status": "success",
            }
    
    Case 3:
        User Input: https://github.com/none-existing-repo

        Tool Calls:
            1. Function Call: aclone_repository_with_retry(repo_name="none-existing-repo")
            Reason: The repository name is the part of the URL that identifies the repository. From the given URL, the repository name is "none-existing-repo". This tool will return an error if the repository is not found.
        Output:
            {
                "status": "error",
                "error": "Failed to clone repository: Repository not found",
            }
    </example>
    """,
    tools=[aclone_repository_with_retry, save_repo_to_db],  # Use the wrapper tool
)
