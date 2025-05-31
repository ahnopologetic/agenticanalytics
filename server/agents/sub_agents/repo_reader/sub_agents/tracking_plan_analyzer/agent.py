from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters



tracking_plan_analyzer_agent = LlmAgent(
    name="tracking_plan_analyzer",
    description="Analyze the tracking plan and generate a tracking plan.",
    instruction="Given git repository path, pack the repository using repomix and search for the tracking plan.",
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
    ],
    output_key="tracking_plan",
)
