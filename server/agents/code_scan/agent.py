from pathlib import Path

from drtail_prompt import load_prompt
from google.adk.agents import Agent
from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
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


if 1 == 1:
    artifact_service = InMemoryArtifactService()  # Choose an implementation
else:
    artifact_service = GcsArtifactService()  # TODO: use GCS artifact service
session_service = InMemorySessionService()

root_agent = Agent(
    model="gemini-2.5-flash-preview-05-20",
    name="code_scan_compression_agent",
    instruction=instruction.messages[0].content,
    tools=[compress_repo, clone_repo],
)

runner = Runner(
    agent=root_agent,
    app_name="code_scan_and_extract",
    artifact_service=artifact_service,
    session_service=session_service,
)
