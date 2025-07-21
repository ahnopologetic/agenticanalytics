import os
from typing import Optional

import agentops
from config import config
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from agents.shared.tools import lc_shell_tool
from google.genai.types import GenerateContentConfig

from agents.sub_agents import (
    event_writer,
    git_manager_agent,
    tracking_code_searcher_agent,
)

if config.agentops_api_key:
    agentops.init(
        config.agentops_api_key,
        trace_name="agentic_analytics",
    )


def _after_agent_callback(callback_context: CallbackContext) -> None:
    state = callback_context.state
    if state["patterns"] is None:
        state.update({"status": "failed"})


# root_agent = SequentialAgent(
#     name="agentic_analytics",
#     description="Analytics Tracking Plan Automation Assistant",
#     sub_agents=[
#         git_manager_agent,
#         tracking_code_searcher_agent,
#         event_writer,
#     ],
#     after_agent_callback=_after_agent_callback,
# )


# understand project -> find tracking code -> write event -> write tracking plan
def list_directory(path: str, depth: int = 1) -> str:
    """
    List the contents of a directory.

    Args:
        path: The path to the directory to list.
        depth: The depth of the directory to list.

    Returns:
        A string representation of the directory contents.
    """
    if depth == 0:
        return ""
    return "\n".join(os.listdir(path))


def read_file(
    path: str, start_line: Optional[int] = None, end_line: Optional[int] = None
) -> str:
    """
    Read a file and return the contents.

    Args:
        path: The path to the file to read.
        start_line: The start line to read.
        end_line: The end line to read.

    Returns:
        A string representation of the file contents.
    """
    with open(path, "r") as f:
        if start_line and end_line:
            if start_line > end_line:
                raise ValueError("Start line must be less than end line")
            lines = f.readlines()
            return "\n".join(lines[start_line - 1 : end_line])
        elif start_line:
            lines = f.readlines()
            return "\n".join(lines[start_line - 1 :])
        else:
            return f.read()


INSTRUCTIONS = """
You are an expert in analytics tracking plan automation.
You are given a project and you need to understand the project and write a tracking plan for it.

<general_instructions>
1. Understand the project and its dependencies.
2. Given dependencies, identify and use patterns to help finding the tracking code in the codebase.
3. Scan the codebase for the tracking codes thoroughly to list down all the tracking codes possible.
4. Write a tracking plan for the tracking codes.
</general_instructions>

<pattern_finding>
Analytics tracking code is usually a combination of a pattern and a unique identifier.
Read the codebase and identify the patterns that are used to track events.
To verify the pattern, you can use ripgrep (rg) with the shell tool.
Make sure you do not print out all the results, only check number of matches:

e.g., rg "<pattern>" <path> -l | wc -l
e.g., rg "trackEvent" src/components/Button.tsx -l | wc -l

List up all the relevant patterns you found. Patterns with the same namespace should be grouped together. For instance, if you find "Mixpanel" and also found "Mixpanel.track" and "Mixpanel.trackEvent", you should group them together into more specific patterns, which is "Mixpanel.track" and "Mixpanel.trackEvent".

</pattern_finding>

<special_instructions>
Your job is to find event tracking patterns in the codebase, not `identify` or `people` codes which are used for other purposes.
Our target usually comes in a pair of event name and event properties.

</special_instructions>

Show the list of patterns you found in json list format. If you cannot find any patterns, return an empty list.

<example>
// if you find the patterns, return them in a list
[
    "Mixpanel.track",
    "Mixpanel.trackEvent",
    "Amplitude.track",
    "Amplitude.trackEvent",
    "Segment.track",
    "Segment.trackEvent",
    "GoogleAnalytics.track",
]

// if you cannot find any patterns, return an empty list
[]

</example>

"""

"""
<tracking_plan>
Use the following schema to write the tracking plan:

<schema>
class AnalyticsTrackEvent(BaseModel):
    name: str = Field(description="The name of the event")
    properties: dict | list | None = Field(description="The properties of the event")
    location: str = Field(description="The location of the event in the codebase", example="src/components/Button.tsx:10")

class AnalyticsTrackPlan(BaseModel):
    events: list[AnalyticsTrackEvent] = Field(description="The events to track")
</schema>

Make sure the output is in JSON format and is valid against the schema.
</tracking_plan>

"""

root_agent = LlmAgent(
    name="agentic_analytics",
    model="gemini-2.5-flash",
    description="Analytics Tracking Plan Automation Assistant",
    instruction=INSTRUCTIONS,
    tools=[
        list_directory,
        read_file,
        lc_shell_tool,
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.0,
    ),
    output_key="patterns",
    after_agent_callback=_after_agent_callback,
)
