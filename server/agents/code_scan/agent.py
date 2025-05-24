from pathlib import Path

from drtail_prompt import load_prompt
from google.adk.agents import Agent
from pydantic import BaseModel

from code_scan.tools.clone_repo import clone_repo
from code_scan.tools.compress_repo import compress_repo

ROOT_DIR = Path(__file__).parent.parent.parent
AGENT_DIR = ROOT_DIR / "agents" / "code_scan"
instruction = load_prompt(AGENT_DIR / "agent_compression.prompt.yaml")


class TrackingAgentOutputItem(BaseModel):
    event_name: str
    properties: dict
    context: str
    location: str


class TrackingAgentOutput(BaseModel):
    items: list[TrackingAgentOutputItem]


root_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="code_scan_compression_agent",
    instruction=instruction.messages[0].content,
    tools=[compress_repo, clone_repo],
)
