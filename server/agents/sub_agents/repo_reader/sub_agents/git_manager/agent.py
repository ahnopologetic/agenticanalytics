from google.adk.agents import LlmAgent

from utils.github import aclone_repository, apull_repository, aswitch_branch

git_manager_agent = LlmAgent(
    name="git_manager_agent",
    model="gemini-2.0-flash",
    description="Manage the git repository.",
    instruction="""
    Given the repository url, clone the repository and stay up to date with the latest changes.

    You have the following tools:
    - aclone_repository(repo_name: str, branch: str = "main"): Clone the repository.
    - apull_repository(repo_path: str): Pull the latest changes.
    - aswitch_branch(repo_path: str, branch: str): Switch to the main branch.

    If you are given a url, you need to extract the repository name and branch from the url.

    If the repository is already cloned, pull the latest changes.
    If the repository is not cloned, clone the repository.
    If the repository is not on the main branch, switch to the main branch.
    """,
    tools=[aclone_repository, apull_repository, aswitch_branch],
    output_key="git_repository_path",
)
