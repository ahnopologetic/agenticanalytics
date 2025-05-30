from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

dba_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="dba",
    instruction="You are a database agent. You are able to answer questions about the database. Using data from state key 'analyzed_tracking_plan', you should store the data in the database.",
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="uvx",
                args=[
                    "mcp-server-sqlite",
                    "--db-path",
                    "./db.sqlite3",
                ],
            ),
        )
    ],
)
