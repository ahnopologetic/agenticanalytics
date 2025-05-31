from pydantic import BaseModel


class TrackingAgentOutput(BaseModel):
    event_name: str
    properties: dict
    context: str
    location: str


class TrackingPlan(BaseModel):
    data: list[TrackingAgentOutput]
