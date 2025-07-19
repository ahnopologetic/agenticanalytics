import structlog
from db_models import Repo
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from pydantic import Field
from utils.db_session import get_db
from utils.github import aclone_repository

logger = structlog.get_logger(__name__)


def save_repo_to_db(
    tool_context: ToolContext,
    repo_name: str,
    branch: str,
):
    """
    Save the repository to the database.
    Args:
        tool_context: ToolContext
        repo_name: str
        branch: str
    Returns:
        None
    """
    db_session = next(get_db())
    try:
        repo = Repo(
            name=repo_name,
            user_id=tool_context.state["user_id"],
            url=f"https://github.com/{repo_name}",
            label=repo_name,
            description=f"Repository {repo_name} cloned from {branch} branch",
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


git_manager_agent = LlmAgent(
    name="git_manager_agent",
    model="gemini-2.0-flash",
    description="Manage the git repository.",
    instruction="""
    Given the repository url, first save the repository to the database and then clone the repository.
    
    Example
    User Input: https://github.com/UnlyEd/next-right-now/tree/master
    1. Function Call: save_repo_to_db(repo_name="UnlyEd/next-right-now", branch="master")
    Reason: Save the repository to the database first.
    2. Function Call: aclone_repository(repo_name="UnlyEd/next-right-now", branch="master")
    Reason: The repository name is the part of the URL that identifies the repository, e.g., "facebook/react" or "UnlyEd/next-right-now". From the given URL, the repository name is "UnlyEd/next-right-now". Also, the branch is master.
    """,
    tools=[aclone_repository, save_repo_to_db],
)
