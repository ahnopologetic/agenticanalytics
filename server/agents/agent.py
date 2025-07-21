import agentops
from config import config
from google.adk.agents import LlmAgent, SequentialAgent

from agents.shared.tools import (
    lc_shell_tool,
    list_directory,
    read_file,
    write_file,
)
from agents.sub_agents import (
    pattern_scanner_agent,
)

if config.agentops_api_key:
    agentops.init(
        config.agentops_api_key,
        trace_name="agentic_analytics",
    )

# new agent to write tracking plan
# based on patterns, go through the codebase and write tracking plan
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
    3. Incrementally write the tracking plan (in jsonnl format) for the analytics tracking events. 
        - Create a new file for each analytics tracking event. Make sure the file name starts with `aatx_` prefix. Only append to the file if the file already exists.
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

    <tools>
    - lc_shell_tool: use the linux shell tool
        - basic linux shell tools: find, grep, etc.
        - analyze-tracking: analytics tracking code finder cli, augmented by AST/treesitter.
            - npx -y @flisk/analyze-tracking /path/to/project [options]
            - Key Options:
                -o, --output <output_file>: Name of the output file (default: tracking-schema.yaml)
                -c, --customFunction <function_name>: Specify a custom tracking function
                --format <format>: Output format, either yaml (default) or json. If an invalid value is provided, the CLI will exit with an error.
                --stdout: Print the output to the terminal instead of writing to a file (works with both YAML and JSON)
        - ripgrep: search the codebase for the tracking events (only for unknown sdk)
    - list_directory: list the directory
    - read_file: read the file
    - write_file: write the file
    </tools>
    """,
    tools=[
        lc_shell_tool,
        list_directory,
        read_file,
        write_file,
    ],
)


root_agent = SequentialAgent(
    name="tracking_plan_discovery_agent",
    description="Analytics Tracking Plan Automation Assistant",
    sub_agents=[
        pattern_scanner_agent,
        tracking_plan_writer_agent,
    ],
)
