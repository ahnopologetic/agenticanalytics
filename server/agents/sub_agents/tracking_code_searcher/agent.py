from google.adk.agents import SequentialAgent
from agents.sub_agents.tracking_code_searcher.sub_agents import (
    dependency_reconnaissance_agent,
    pattern_matching_analyze_tracking_agent,
)
from google.adk.agents.callback_context import CallbackContext


def after_agent_callback(callback_context: CallbackContext) -> None:
    # set state including:
    # - tracking_code_searcher_output
    # - tracking_code_searcher_output_valid
    # - status
    # - repository id in db
    ...


tracking_code_searcher_agent = SequentialAgent(
    name="tracking_code_searcher_agent",
    sub_agents=[
        dependency_reconnaissance_agent,
        pattern_matching_analyze_tracking_agent,
    ],
    after_agent_callback=after_agent_callback,
)

root_agent = tracking_code_searcher_agent
