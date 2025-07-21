from pathlib import Path
import structlog
from config import config
from drtail_prompt import load_prompt
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from pydantic import BaseModel, ValidationError

from agents.shared.tools import lc_shell_tool

logger = structlog.get_logger(__name__)


class Pattern(BaseModel):
    pattern: str
    output_file: Path


class PatternMatchingAnalyzeTrackingOutput(BaseModel):
    patterns: list[Pattern]


def validate_pattern_matching_analyze_tracking_input(
    callback_context: CallbackContext,
) -> None:
    if "dependency_reconnaissance_output" not in callback_context.state:
        raise ValueError("Dependency reconnaissance output is not found")
    if callback_context.state["dependency_found"] is False:
        raise ValueError("No tracking SDK is found")


def validate_pattern_matching_analyze_tracking_output(
    callback_context: CallbackContext,
) -> None:
    message = callback_context.state["pattern_matching_analyze_tracking_output"]
    if message.startswith("```json"):
        message = message[7:]
    if message.endswith("```"):
        message = message[:-3]
    message = message.strip()
    logger.info("Pattern matching analyze tracking output", message=message)

    try:
        output = PatternMatchingAnalyzeTrackingOutput.model_validate_json(message)
    except ValidationError:
        callback_context.state.update(
            {
                "pattern_matching_analyze_tracking_output": [],
                "pattern_matching_analyze_tracking_output_valid": False,
            }
        )
        logger.error(
            "Pattern matching analyze tracking output is not valid",
            agent_name=callback_context.agent_name,
            output=message,
        )
        return
    logger.info(
        f"[{callback_context.agent_name}] Pattern matching analyze tracking output: {message}"
    )

    callback_context.state.update(
        {
            "pattern_matching_analyze_tracking_output": output.model_dump_json(),
            "pattern_matching_analyze_tracking_output_valid": True,
            "status": "pattern_found",
        }
    )


prompt = load_prompt(config.pattern_matching_analyze_tracking_agent_prompt_path)

pattern_matching_analyze_tracking_agent = LlmAgent(
    name="pattern_matching_analyze_tracking_agent",
    description="A agent that can analyze tracking code",
    model="gemini-2.0-flash",
    instruction=prompt.messages[0].content,
    tools=[lc_shell_tool],
    output_key="pattern_matching_analyze_tracking_output",
    before_agent_callback=validate_pattern_matching_analyze_tracking_input,
    after_agent_callback=validate_pattern_matching_analyze_tracking_output,
    generate_content_config=types.GenerateContentConfig(temperature=0.1),
)
