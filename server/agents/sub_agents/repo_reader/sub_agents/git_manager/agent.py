import asyncio  # For async operations and delays
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
):
    """
    Save the repository to the database.
    Args:
        tool_context: ToolContext
        repo_name: str
        branch: Optional[str] - the branch to clone the repository
    Returns:
        None
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
        return

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


# --- New Wrapper Tool for aclone_repository with Retry Logic ---
async def aclone_repository_with_retry(
    tool_context: ToolContext,
    repo_name: str,
    branch: Optional[str] = None,  # Initial branch, can be None
):
    """
    Attempts to clone a repository, retrying with common alternative branches
    if the initial attempt fails due to a branch not found error.

    Args:
        tool_context: ToolContext
        repo_name: str
        branch: Optional[str]
    Returns:
        str - the path to the cloned repository
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
            await aclone_repository(
                tool_context=tool_context,
                repo_name=repo_name,
                branch=current_branch,
            )
            logger.info(
                f"Successfully cloned {repo_name} with branch: {current_branch}"
            )
            tool_context.state["cloned_branch"] = (
                current_branch  # Store the successfully used branch
            )
            return  # Success!
        except Exception as e:
            # IMPORTANT: You need to inspect the exception type/message from `aclone_repository`
            # to determine if it's a "branch not found" error.
            # Replace `SpecificBranchNotFoundError` with the actual exception from your `utils.github`
            # or check `e.message` if it's a generic exception.
            is_branch_not_found_error = False
            if (
                f"branch {current_branch} not found" in str(e).lower()
                or "reference not found" in str(e).lower()
            ):  # Generic check
                is_branch_not_found_error = True
            # if isinstance(e, SpecificBranchNotFoundError): # If aclone_repository raises a specific error
            #     is_branch_not_found_error = True

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
                # If it's the last attempt or not a "branch not found" error, re-raise
                raise  # Re-raise the original exception if retries are exhausted or it's a different error

    # If we get here, it means all attempts failed and an exception was re-raised on the last attempt.
    # This return is mostly for type hinting; the raise should prevent reaching here.
    raise Exception(f"Failed to clone {repo_name} after exhausting all branch options.")


git_manager_agent = LlmAgent(
    name="git_manager_agent",
    model="gemini-2.0-flash",
    description="Manage the git repository.",
    instruction="""
    Given the repository url, first save the repository to the database and then clone the repository.
    If the user input is a branch, then use the branch name to clone the repository.

    **Important:** When cloning the repository, use the `aclone_repository_with_retry` tool. This tool
    will intelligently attempt to clone, trying common alternative branches like 'main' or 'master'
    if the initial attempt or inferred branch fails.

    Example
    User Input: https://github.com/UnlyEd/next-right-now/tree/main
    1. Function Call: save_repo_to_db(repo_name="UnlyEd/next-right-now", branch="main")
    Reason: Save the repository to the database first.
    2. Function Call: aclone_repository_with_retry(repo_name="UnlyEd/next-right-now", branch="main")
    Reason: The repository name is the part of the URL that identifies the repository, e.g., "facebook/react" or "UnlyEd/next-right-now". From the given URL, the repository name is "UnlyEd/next-right-now". This tool handles retries with alternative branches.

    User Input: https://github.com/UnlyEd/next-right-now
    1. Function Call: save_repo_to_db(repo_name="UnlyEd/next-right-now")
    Reason: Save the repository to the database first.
    2. Function Call: aclone_repository_with_retry(repo_name="UnlyEd/next-right-now")
    Reason: The repository name is the part of the URL that identifies the repository, e.g., "facebook/react" or "UnlyEd/next-right-now". From the given URL, the repository name is "UnlyEd/next-right-now". This tool handles retries with alternative branches.
    """,
    tools=[aclone_repository_with_retry, save_repo_to_db],  # Use the wrapper tool
)
