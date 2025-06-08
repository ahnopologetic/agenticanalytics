from langchain_community.tools import ShellTool
from google.adk.tools.langchain_tool import LangchainTool

shell_tool = ShellTool(
    name="shell_tool",
)

lc_shell_tool = LangchainTool(
    tool=shell_tool,
    name="shell_tool",
    description="A tool that can run shell commands",
)
