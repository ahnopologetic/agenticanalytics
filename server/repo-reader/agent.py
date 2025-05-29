from pathlib import Path
from drtail_prompt import load_prompt
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from pydantic import BaseModel

ROOT_DIR = Path(__file__).parent.parent
AGENT_DIR = ROOT_DIR / "repo-reader"
instruction = load_prompt(AGENT_DIR / "agent-compression.prompt.yaml")


class TrackingAgentOutput(BaseModel):
    event_name: str
    properties: dict
    context: str
    location: str

class TrackingPlan(BaseModel):
    data: list[TrackingAgentOutput]

repo_reader_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="repo_reader",
    instruction=instruction.messages[0].content,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "repomix",
                    "--mcp",
                ],
            ),
        )
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
