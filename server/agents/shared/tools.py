import os
from typing import Optional
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


def write_file(path: str, content: str) -> str:
    """
    Write a file and return the contents.
    """
    with open(path, "w") as f:
        f.write(content)
    return content
