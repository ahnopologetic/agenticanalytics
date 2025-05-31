from google.adk.agents import SequentialAgent
from agents.sub_agents import repo_reader_agent, dba_agent


root_agent = SequentialAgent(
    name="root",
    description="Analytics Tracking Plan Automation Assistant",
    sub_agents=[repo_reader_agent, dba_agent],
)
