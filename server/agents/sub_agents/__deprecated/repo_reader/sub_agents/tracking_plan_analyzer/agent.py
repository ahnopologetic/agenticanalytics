import json
import os
from drtail_prompt import load_prompt
from google.adk.agents import LlmAgent, LoopAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
import structlog
from config import config

repomix_agent_prompt = load_prompt(config.repomix_agent_prompt_path)

logger = structlog.get_logger(__name__)


def _sanitize_analytics_code(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> str:
    """
    Sanitize the analytics code to remove any sensitive information.
    """
    if not llm_response.content or not llm_response.content.parts:
        return llm_response
    if not llm_response.content.parts[0].text:
        return llm_response
    logger.info(f"Sanitizing analytics code: {llm_response.content.parts[0].text[:20]}")
    callback_context.state["status"] = "analyzed"
    return llm_response


def combine_tracking_plans(tool_context: ToolContext, tracking_plans: str) -> dict:
    """
    Combine the tracking plans into a single tracking plan.

    Args:
        tool_context: The tool context.
        tracking_plans: The tracking plans.

    Returns:
        A dictionary with the new events and existing events.
    """
    # validate
    state = tool_context.state
    current_tracking_plans = state.get("tracking_plans", [])

    try:
        new_tracking_plans = json.loads(tracking_plans)
    except json.JSONDecodeError:
        logger.error(f"Invalid tracking plans: {tracking_plans}")
        raise ValueError(f"Invalid tracking plans: {tracking_plans}")

    # TODO: validate the tracking plans

    result = {
        "new_events": [],
        "existing_events": [],
    }

    for tracking_plan in new_tracking_plans:
        if tracking_plan["event_name"] in current_tracking_plans:
            result["existing_events"].append(tracking_plan)
            continue

        result["new_events"].append(tracking_plan)
        current_tracking_plans.append(tracking_plan)

    tool_context.state["tracking_plans"] = current_tracking_plans

    return result


repomix_agent = LlmAgent(
    name="repomix_agent",
    description="Pack the repository and search for analytics code using repomix.",
    instruction=repomix_agent_prompt.messages[0].content,
    model="gemini-2.0-flash",  # TODO: use claude 3.5 sonnet
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
        ),
        combine_tracking_plans,
    ],
    after_model_callback=_sanitize_analytics_code,
)


def _before_agent_callback(callback_context: CallbackContext) -> None:
    """
    Before the agent is called, set the state.
    """
    state = callback_context.state
    git_repository_path = state.get("git_repository_path")
    if not git_repository_path:
        callback_context.state["status"] = "failed"
        raise ValueError("Git repository path is not set")

    # check if the repository is cloned
    if not os.path.exists(git_repository_path):
        callback_context.state["status"] = "failed"
        raise ValueError("Git repository is not cloned")


tracking_plan_analyzer_agent = LoopAgent(
    name="tracking_plan_analyzer_agent",
    description="Tracking plan analyzer",
    sub_agents=[repomix_agent],
    max_iterations=5,
    before_agent_callback=_before_agent_callback,
)
