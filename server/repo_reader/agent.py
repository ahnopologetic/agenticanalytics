import structlog
from config import config
from drtail_prompt import load_prompt
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools.tool_context import ToolContext
from pydantic import BaseModel
from utils.github import aclone_repository

repo_reader_agent_prompt = load_prompt(config.repo_reader_prompt_path)


class TrackingAgentOutput(BaseModel):
    event_name: str
    properties: dict
    context: str
    location: str


class TrackingPlan(BaseModel):
    data: list[TrackingAgentOutput]


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


repo_reader_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="repo_reader",
    instruction=repo_reader_agent_prompt.messages[0].content,
    tools=[
        aclone_repository,
        MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "repomix",
                    "--mcp",
                ],
            ),
        ),
        save_repomix_artifact,
    ],
    output_key="analyzed_tracking_plan",
)
dba_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="dba",
    instruction="You are a database agent. You are able to answer questions about the database. Using data from state key 'analyzed_tracking_plan', you should store the data in the database.",
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="uvx",
                args=[
                    "mcp-server-sqlite",
                    "--db-path",
                    "./db.sqlite3",
                ],
            ),
        )
    ],
)
root_agent = SequentialAgent(
    name="root",
    description="Analytics Tracking Plan Automation Assistant",
    sub_agents=[repo_reader_agent, dba_agent],
)
