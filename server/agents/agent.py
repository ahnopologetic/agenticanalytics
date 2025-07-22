import agentops
from config import config
from google.adk.agents import SequentialAgent

from agents.sub_agents import (
    pattern_scanner_agent,
    tracking_plan_writer_agent,
)

if config.agentops_api_key:
    agentops.init(
        config.agentops_api_key,
        trace_name="agentic_analytics",
    )


root_agent = SequentialAgent(
    name="tracking_plan_discovery_agent",
    description="Analytics Tracking Plan Automation Assistant",
    sub_agents=[
        pattern_scanner_agent,
        tracking_plan_writer_agent,
    ],
)
