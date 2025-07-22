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


def list_directory(path: str, depth: int = 1, per_level_limit: int = 10) -> str:
    """
    Recursively list the contents of a directory up to a specified depth.

    Args:
        path: The path to the directory to list.
        depth: The depth of the directory to list.
        per_level_limit: The maximum number of items to list per level.

    Returns:
        A string representation of the directory contents.
    """
    if depth <= 0:
        return ""
    if not os.path.isdir(path):
        return f"{path} [Not a directory]"
    result = []
    try:
        for entry in os.listdir(path):
            entry_path = os.path.join(path, entry)
            result.append(entry_path)
            if os.path.isdir(entry_path) and depth > 1:
                sub_result = list_directory(entry_path, depth - 1, per_level_limit)
                if len(sub_result) > per_level_limit:
                    result.append(f"... {len(sub_result) - per_level_limit} more")
                else:
                    result.append(sub_result)
    except Exception as e:
        result.append(f"Error accessing {path}: {e}")
    return "\n".join(result)


def read_file(
    path: str, start_line: Optional[int] = None, end_line: Optional[int] = None
) -> str:
    """
    Read a file and return the contents, upto 250 lines.

    Args:
        path: The path to the file to read.
        start_line: The start line to read.
        end_line: The end line to read.

    Returns:
        A string representation of the file contents.
    """
    if start_line and end_line:
        if end_line - start_line > 250:
            raise ValueError("End line must be less than 250 lines from start line")

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
            lines = f.readlines()
            if len(lines) > 250:
                return "\n".join(
                    lines[:250] + [f"... {len(lines) - 250} more"]
                )
            else:
                return "\n".join(lines)


def edit_file(path: str, content: str, auto_apply: bool = True) -> str:
    """
    Suggests an edit to a file by showing the diff, and optionally applies the edit.

    Args:
        path: The path to the file to edit.
        content: The new content to write to the file.
        auto_apply: If True, automatically apply the edit. If False, only show the suggestion.

    Returns:
        The new content if applied, or a suggestion message.
    """
    import difflib
    import os

    if not os.path.exists(path):
        old_lines = []
    else:
        with open(path, "r") as f:
            old_lines = f.readlines()

    new_lines = content.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines, new_lines, fromfile=path, tofile=path, lineterm=""
    )
    diff_text = "\n".join(diff)

    if not diff_text:
        return "No changes detected."

    suggestion = f"Suggested changes to {path}:\n{diff_text}"

    if auto_apply:
        with open(path, "w") as f:
            f.write(content)
        return f"{suggestion}\n\nChanges applied."
    else:
        return suggestion
