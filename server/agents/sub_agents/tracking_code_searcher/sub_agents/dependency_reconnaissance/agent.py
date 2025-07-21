from pathlib import Path
from typing import Literal

from drtail_prompt import load_prompt
from pydantic import BaseModel, Field, ValidationError
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from google.adk.agents.run_config import RunConfig
from google.adk.agents import LlmAgent
from config import config
import structlog

from agents.shared.tools import lc_shell_tool

logger = structlog.get_logger(__name__)


class DependencyReconnaissanceOutput(BaseModel):
    project_path: Path
    tracking_sdk: Literal[
        "google_analytics",
        "firebase_analytics",
        "gtag",
        "segment",
        "mixpanel",
        "amplitude",
        "rudderstack",
        "mparticle",
        "posthog",
        "pendo",
        "heap",
        "snowplow",
    ] = Field(..., description="The tracking SDK used in the project")
    package_file_path: Path
    language: Literal[
        "javascript", "typescript", "swift", "kotlin", "ruby", "go", "python"
    ]


def validate_dependency_reconnaissance_output(
    callback_context: CallbackContext,
) -> None:
    message = callback_context.state["dependency_reconnaissance_output"]
    if message.startswith("```json"):
        message = message[7:]
    if message.endswith("```"):
        message = message[:-3]
    message = message.strip()
    logger.info("Dependency reconnaissance output", message=message)

    try:
        output = DependencyReconnaissanceOutput.model_validate_json(message)
    except ValidationError:
        logger.error(
            "Dependency reconnaissance output is not valid",
            agent_name=callback_context.agent_name,
            output=message,
        )
        callback_context.state.update({"dependency_found": False})
        raise
    logger.info(
        f"[{callback_context.agent_name}] Dependency found: {output.model_dump_json()}",
        agent_name=callback_context.agent_name,
    )
    callback_context.state.update(
        {
            "dependency_found": True,
            "dependency_reconnaissance_output": output.model_dump_json(),
            "status": "sdk_found",
        }
    )


prompt = load_prompt(config.dependency_reconnaissance_agent_prompt_path)
config = RunConfig(max_llm_calls=10)
dependency_reconnaissance_agent = LlmAgent(
    name="dependency_reconnaissance_agent",
    description="A agent that can find dependencies between different tools and services",
    model="gemini-2.5-flash",
    instruction=prompt.messages[0].content,
    tools=[lc_shell_tool],
    output_key="dependency_reconnaissance_output",
    after_agent_callback=validate_dependency_reconnaissance_output,
    generate_content_config=types.GenerateContentConfig(temperature=0.1),
)
