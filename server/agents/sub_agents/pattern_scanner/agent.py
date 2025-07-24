from agents.shared.tools import lc_shell_tool, list_directory, read_file
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai.types import GenerateContentConfig


def _after_agent_callback(callback_context: CallbackContext) -> None:
    state = callback_context.state
    if state["patterns"] is None:
        state.update(
            {
                "status": {
                    "pattern_scanning": "failed",
                    "tracking_plan_writing": "not_started",
                },
                "reason": "Unexpected error",
            }
        )
    elif state["patterns"] == []:
        state.update(
            {
                "status": {
                    "pattern_scanning": "failed",
                    "tracking_plan_writing": "not_started",
                },
                "reason": "No patterns found",
            }
        )
    else:
        state.update(
            {
                "status": {
                    "pattern_scanning": "completed",
                    "tracking_plan_writing": "not_started",
                }
            }
        )


INSTRUCTION = """
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

Besides, focus on pulling out as many patterns as possible. Breadth first search is preferred.
When you find a pattern, you should also find the patterns that are related to it.
Use ripgrep to find the relevant patterns.

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


pattern_scanner_agent = LlmAgent(
    name="pattern_scanner",
    model="gemini-2.5-flash",
    description="Analytics Tracking Plan Automation Assistant",
    instruction=INSTRUCTION,
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
