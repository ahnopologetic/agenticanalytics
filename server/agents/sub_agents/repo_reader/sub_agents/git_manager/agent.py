from google.adk.agents import LlmAgent

from utils.github import aclone_repository

git_manager_agent = LlmAgent(
    name="git_manager_agent",
    model="gemini-2.0-flash",
    description="Manage the git repository.",
    instruction="""
    Given the repository url, clone the repository using the aclone_repository tool.
    
    Example
    User Input: https://github.com/UnlyEd/next-right-now/tree/master
    Function Call: aclone_repository(repo_name="UnlyEd/next-right-now", branch="master")
    Reason: The repository name is the part of the URL that identifies the repository, e.g., "facebook/react" or "UnlyEd/next-right-now". From the given URL, the repository name is "UnlyEd/next-right-now". Also, the branch is master.
    """,
    tools=[aclone_repository],
)
