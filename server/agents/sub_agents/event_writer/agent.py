import json
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
import structlog

from agents.shared.analyze_tracking import (
    AnalyzeTrackingYaml,
    parse_analyze_tracking_yaml,
)
from db_models import UserEvent
from utils.db_session import get_db

logger = structlog.get_logger(__name__)


async def read_analyze_tracking_yaml(
    tool_context: ToolContext,
) -> list[AnalyzeTrackingYaml]:
    """
    Read the analyze tracking yaml file.
    """
    patterns_str = tool_context.state["pattern_matching_analyze_tracking_output"]
    logger.info("pattern is handled by event writer", patterns_str=patterns_str)
    patterns = json.loads(patterns_str)["patterns"]
    outputs = []

    for pattern in patterns:
        # calling_pattern = pattern["pattern"]
        output_file = pattern["output_file"]

        try:
            output = parse_analyze_tracking_yaml(output_file)
        except ValueError as e:
            logger.error(
                "error parsing analyze tracking yaml", error=e, output_file=output_file
            )
            continue
        outputs.append(output)

    return outputs


async def write_events_to_db(
    tool_context: ToolContext,
    events: list[AnalyzeTrackingYaml],
) -> None:
    """
    Write the events to the database.
    """
    logger.info("writing events to db", events=len(events))
    db_session = next(get_db())
    try:
        events_to_write = []
        for event in events:
            for event_name, event_data in event.events.items():
                events_to_write.append(
                    UserEvent(
                        repo_id=tool_context.state["repo_id"],
                        event_name=event_name,
                        context=event_data.context,
                        tags=event_data.tags,
                        file_path=event_data.implementations[0].path,
                        line_number=event_data.implementations[0].line,
                    )
                )
        db_session.add_all(events_to_write)  # TODO: use upsert
        db_session.commit()
    except Exception as e:
        logger.error(f"Error writing events to database: {e}")
        raise e
    finally:
        db_session.close()


async def write_event(tool_context: ToolContext):
    """
    Write the event to the database.
    """

    analyze_tracking_yaml = await read_analyze_tracking_yaml(tool_context)
    await write_events_to_db(tool_context, analyze_tracking_yaml)


event_writer = LlmAgent(
    name="event_writer",
    model="gemini-2.0-flash",
    description="Write events to the database.",
    instruction="""
    Given the repository id, write the events to the database.

    {{ pattern_matching_analyze_tracking_output }}

    ### Output
    - Write the events to the database.
    """,
    tools=[write_event],
)
