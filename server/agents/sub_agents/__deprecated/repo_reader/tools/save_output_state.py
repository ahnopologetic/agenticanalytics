from google.adk.tools import ToolContext
from pydantic import ValidationError
import structlog

from agents.schema import TrackingPlan

logger = structlog.get_logger(__name__)


async def save_output_state(tool_context: ToolContext, output: dict):
    """
    Save the output state as an artifact.
    """
    try:
        tracking_plan = TrackingPlan(data=output)
    except ValidationError as e:
        logger.error(f"Invalid output: {e}")
        raise e

    tool_context.state["analyzed_tracking_plan"] = tracking_plan.model_dump()
