from pathlib import Path
import shutil

from code_scan.ingestion.rag_corpus import clone_github_repo
from code_scan.ingestion.config import config
import structlog

logger = structlog.get_logger()


def clone_repo(repo_url: str, local_target_path_str: str = config.local_repo_path):
    """Clone a repository from a URL to a local path

    Args:
        repo_url: The URL of the repository to clone
        local_target_path: The path to the target repository.

    Returns:
        The path to the target repository
    """

    if isinstance(local_target_path_str, str):
        local_target_path = Path(local_target_path_str)

    if local_target_path.exists():
        logger.info("Repository already cloned", path=local_target_path.as_posix())
        return local_target_path.as_posix()

    local_repo_path = clone_github_repo(repo_url)

    if not local_repo_path.exists():
        raise FileNotFoundError(
            f"Repository path {local_repo_path.as_posix()} does not exist"
        )

    shutil.copytree(local_repo_path, local_target_path)

    # clean up the local repo path
    shutil.rmtree(local_repo_path)

    return local_target_path.as_posix()
