from agents.sub_agents.repo_reader.tools.save_output_state import save_output_state
from agents.sub_agents.repo_reader.tools.save_repomix_artifact import (
    save_repomix_artifact,
)
from config import config
from drtail_prompt import load_prompt
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai.types import GenerateContentConfig
from utils.github import aclone_repository

repo_reader_agent_prompt = load_prompt(config.repo_reader_prompt_path)


repo_reader_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="repo_reader",
    instruction=repo_reader_agent_prompt.messages[0].content,
    tools=[
        aclone_repository,
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
        save_repomix_artifact,
        save_output_state,
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.0,
    ),
)
