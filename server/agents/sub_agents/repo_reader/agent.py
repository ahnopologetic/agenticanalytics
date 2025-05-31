from sub_agents.git_manager.agent import git_manager_agent
from sub_agents.tracking_plan_analyzer.agent import (
    tracking_plan_analyzer_agent,
)
from google.adk.agents import SequentialAgent


repo_reader_agent = SequentialAgent(
    name="repo_reader",
    description="Clone the repository and analyze the tracking plan.",
    sub_agents=[
        git_manager_agent,
        tracking_plan_analyzer_agent,
    ],
)
