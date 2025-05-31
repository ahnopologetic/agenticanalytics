import os
from pathlib import Path
import shutil
import uuid
import zipfile

import google.genai.types as types


from rag.ingestion.rag_corpus import clone_github_repo
from rag.ingestion.config import config
import structlog
from google.adk.tools import ToolContext

logger = structlog.get_logger()


async def clone_repo(
    tool_context: ToolContext,
    session_id: str,
    repo_url: str,
    local_target_path_str: str = config.local_repo_path,
):
    """Clone a repository from a URL to a local path

    Args:
        repo_url: The URL of the repository to clone
        local_target_path: The path to the target repository.

    Returns:
        The path to the target repository
    """
    logger.info("Session ID", session_id=session_id)
    assert session_id is not None, "Session ID is required"

    if isinstance(local_target_path_str, str):
        local_target_path = Path(local_target_path_str)

    if local_target_path.exists():
        logger.info("Repository already cloned", path=local_target_path.as_posix())
        return local_target_path.as_posix()

    local_repo_path, commit_hash = clone_github_repo(repo_url)

    if not local_repo_path.exists():
        raise FileNotFoundError(
            f"Repository path {local_repo_path.as_posix()} does not exist"
        )

    if local_target_path == local_repo_path:
        logger.info("Repository already cloned", path=local_target_path.as_posix())
        # save it to adk artifact
    else:
        shutil.copytree(local_repo_path, local_target_path)
        shutil.rmtree(local_repo_path)

    # get local target path zip file
    zip_file_path = local_target_path.as_posix() + ".zip"
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(local_target_path):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.join(root, file))

    temp_user_id = session_id  # TODO: replace with user id
    temp_artifact_name = f"user:{temp_user_id}:{local_target_path.name}"

    with open(zip_file_path, "rb") as f:
        data = f.read()

    repo_artifact = types.Part(
        inline_data=types.Blob(
            display_name=temp_artifact_name,
            mime_type="application/zip",
            data=data,
        )
    )
    await tool_context.save_artifact(temp_artifact_name, repo_artifact)

    return local_target_path.as_posix()
