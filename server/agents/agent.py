from google.adk.agents import SequentialAgent
from google.adk.agents.callback_context import CallbackContext

from agents.sub_agents import (
    git_manager_agent,
    tracking_code_searcher_agent,
)


def _after_agent_callback(callback_context: CallbackContext) -> None:
    state = callback_context.state
    if state["status"] == "failed":
        raise ValueError("Failed to complete the task")

    callback_context.state["status"] = "completed"


root_agent = SequentialAgent(
    name="agentic_analytics",
    description="Analytics Tracking Plan Automation Assistant",
    sub_agents=[
        git_manager_agent,
        tracking_code_searcher_agent,
    ],
    after_agent_callback=_after_agent_callback,
)
