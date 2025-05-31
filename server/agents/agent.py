from google.adk.agents import SequentialAgent
from agents.sub_agents import repo_reader_agent, dba_agent
from google.adk.agents.callback_context import CallbackContext


def _after_agent_callback(callback_context: CallbackContext) -> None:
    state = callback_context.state
    if state["status"] == "failed":
        raise ValueError("Failed to complete the task")

    callback_context.state["status"] = "completed"


root_agent = SequentialAgent(
    name="root",
    description="Analytics Tracking Plan Automation Assistant",
    sub_agents=[repo_reader_agent, dba_agent],
    after_agent_callback=_after_agent_callback,
)
