import json
import os
from google.adk.agents import LlmAgent
from google.genai.types import GenerateContentConfig

from agents.shared.tools import (
    edit_file,
    lc_shell_tool,
    list_directory,
    read_file,
)


def convert_analyze_tracking_output_to_tracking_plan(
    analyze_tracking_output_file_path: str,
    target_file_path: str,
) -> str:
    """
    Convert the output of analyze-tracking to a tracking plan.

    Args:
        analyze_tracking_output_file_path: The path to the analyze-tracking output file.
        target_file_path: The path to the target file to write the tracking plan to.

    Returns:
        The tracking plan. If the file exists, append; otherwise, create and write.
    """
    if not os.path.exists(analyze_tracking_output_file_path):
        return f"Analyze tracking output file {analyze_tracking_output_file_path} not found"

    with open(analyze_tracking_output_file_path, "r", encoding="utf-8") as f:
        output = json.load(f)

    if not output["events"] or output["events"] == {}:
        return "No tracking events found"

    tracking_plan = []
    for event_name, event_data in output["events"].items():
        tracking_plan.append(
            {
                "name": event_name,
                "description": "",
                "location": f"{event_data['implementations'][0]['path']}:{event_data['implementations'][0]['line']}",  # TODO: use multiple locations if there are multiple implementations
                "properties": [
                    {
                        "property_name": property_name,
                        "property_type": property_data["type"],
                        "property_description": "",
                    }
                    for property_name, property_data in event_data["properties"].items()
                ],
            }
        )

    # Output each event as a JSON object on a single line (JSON Lines format)
    # If the file exists, append; otherwise, create and write
    mode = "a" if os.path.exists(target_file_path) else "w"
    with open(target_file_path, mode, encoding="utf-8") as f:
        for event in tracking_plan:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return f"Tracking plan written to {target_file_path} ({len(tracking_plan)} events)"


# TODO: combine json nl files into a single file, and sync with database
tracking_plan_writer_agent = LlmAgent(
    name="tracking_plan_writer",
    description="Analytics Tracking Plan Automation Assistant",
    model="gemini-2.5-flash",
    instruction="""
    You are an expert in analytics tracking plan automation.
    You are given a list of patterns and you need to read the codebase and write a tracking plan for it.

    <general_instructions>
    1. Understand the project and its dependencies.
    2. Given patterns, read the codebase and identify the analytics tracking events.
        - For known sdk, you can use `analyze-tracking` command to scan the codebase for the tracking events.
        - For unknown sdk, you should use basic linux shell tools (including ripgrep, find, and more advanced tools) to scan the codebase for the tracking events. 
    3. Incrementally write the tracking plan (in json new line format) for the analytics tracking events. 
        - Create a new file (aatx_<project_name>.json) for each analytics tracking event. Make sure the file name starts with `aatx_` prefix. Keep them in a single file, appending to the file if it already exists.
        - Read current tracking plan and update the tracking plan using the tools provided.
    </general_instructions>

    <analytics_tracking_event>
    Analytics tracking event is an object with the following fields:
    - name: string, the name of the analytics tracking event, can be any case based on internal convention
    - description: string, the description of the analytics tracking event
    - location: string, the location of the analytics tracking event in the codebase
    - properties: array of objects, the properties of the analytics tracking event
        - property_name: string, the name of the property
        - property_type: string, the type of the property
        - property_description: string, the description of the property
    
    <example>
    {
        "name": "User Signed Up",
        "description": "User signed up",
        "location": "src/components/Button.tsx",
        "properties": []
    }

    {
        "name": "user_signed_up",
        "description": "User signed up",
        "location": "src/components/Button.tsx",
        "properties": [
            {
                "property_name": "user_id",
                "property_type": "string",
                "property_description": "The id of the user"
            },
            {
                "property_name": "user_name",
                "property_type": "string",
                "property_description": "The name of the user"
            }
        ]
    }
    </example>
    </analytics_tracking_event>

    <known_sdk>
    - mixpanel: https://docs.mixpanel.com/docs/what-is-mixpanel
    - segment: https://segment.com/docs/connections/spec/track/
    - google analytics: https://developers.google.com/analytics/devguides/collection/ga4/reference/events
    - google tag manager: https://developers.google.com/tag-manager/reference/events
    - amplitude: https://developers.amplitude.com/reference/events
    - posthog: https://posthog.com/docs/libraries/python#events
    - heap: https://docs.heap.io/reference/events
    - customer.io: https://docs.customer.io/docs/events/
    - klaviyo: https://developers.klaviyo.com/reference/events
    - mparticle: https://docs.mparticle.com/
    - snowplow: https://docs.snowplow.io/docs/collecting-data/collecting-from-own-applications/
    - pendo: https://developers.pendo.io/
    - datadog RUM: https://docs.datadoghq.com/real_user_monitoring/
    </known_sdk>

    <tools>
    - lc_shell_tool: standard linux shell tools. Use this to find the tracking events in the codebase. For known sdk, use this tool to create a detected tracking events file and use this created file to update the tracking plan.
        - analyze-tracking: analytics tracking code finder cli, augmented by AST/treesitter. 
            - npx -y @flisk/analyze-tracking /path/to/project [options]
            - Key Options:
                -o, --output <output_file>: Name of the output file 
                -c, --customFunction <function_name>: Specify a custom tracking function
                --format <format>: Output format, either yaml (default) or json. If an invalid value is provided, the CLI will exit with an error.
        - ripgrep: search the codebase for the tracking events (only for unknown sdk)
    - list_directory: list the directory. Use this to understand the codebase structure for the tracking events.
        args:
            - path: The path to the directory to list.
            - depth: The depth of the directory to list.
            - per_level_limit: The maximum number of items to list per level.
        returns:
            - The contents of the directory.
    - read_file: read the file up to 250 lines. If you didn't find the content you need, adjust start and end line numbers. Use this to scan the codebase for the tracking events.
        args:
            - path: The path to the file to read.
            - start_line(optional): The line number to start reading from.
            - end_line(optional): The line number to stop reading at.
        returns:
            - The contents of the file.
    - edit_file: edit the file. Use this to update the tracking plan.
        args:
            - path: The path to the file to edit.
            - content: The new content to write to the file.
            - auto_apply: If True, automatically apply the edit. If False, only show the suggestion.
        returns:
            - The new content if applied, or a suggestion message.
    - convert_analyze_tracking_output_to_tracking_plan: convert the output of analyze-tracking to a tracking plan. Use this to convert the output of analyze-tracking to a tracking plan.
        args:
            - analyze_tracking_output_file_path: The path to the analyze-tracking output file.
            - target_file_path: The path to the target file to write the tracking plan to.
        returns:
            - The tracking plan.
    </tools>
    """,
    tools=[
        lc_shell_tool,
        list_directory,
        read_file,
        edit_file,
        convert_analyze_tracking_output_to_tracking_plan,
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.0,
    ),
)
