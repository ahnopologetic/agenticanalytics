from google.adk.agents import SequentialAgent
from agents.sub_agents.tracking_code_searcher.sub_agents import (
    dependency_reconnaissance_agent,
    pattern_matching_analyze_tracking_agent,
)


tracking_code_searcher_agent = SequentialAgent(
    name="tracking_code_searcher_agent",
    sub_agents=[
        dependency_reconnaissance_agent,
        pattern_matching_analyze_tracking_agent,
    ],
)

root_agent = tracking_code_searcher_agent
