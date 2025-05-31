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

    If you are given a url, you need to extract the repository name and branch from the url.

    If the repository is not cloned, clone the repository.
    """,
    tools=[aclone_repository],
)
