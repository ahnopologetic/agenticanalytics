from google.adk.tools import ToolContext
import structlog

logger = structlog.get_logger(__name__)


async def save_repomix_artifact(
    tool_context: ToolContext, repomix_file_path: str, mime_type: str
):
    """
    Save a repomix file as an artifact.
    """
    import google.genai.types as types

    with open(repomix_file_path, "rb") as f:
        filename = repomix_file_path.split("/")[-1]
        artifact = types.Part(
            inline_data=types.Blob(mime_type=mime_type, data=f.read())
        )
        version = await tool_context.save_artifact(filename=filename, artifact=artifact)
        logger.info(f"Saved artifact {filename} with version {version}")

    return {"status": "success", "repomix_file_path": repomix_file_path}
