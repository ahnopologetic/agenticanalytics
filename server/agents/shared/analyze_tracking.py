from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AnalyzeTrackingYamlSource(BaseModel):
    repository: str
    commit: str
    timestamp: datetime


class AnalyzeTrackingYamlEventImplementation(BaseModel):
    path: str
    line: int
    function: str
    destination: Optional[str] = None


class AnalyzeTrackingYamlEventProperty(BaseModel):
    type: str
    description: Optional[str] = None


class AnalyzeTrackingYamlEvent(BaseModel):
    implementations: list[AnalyzeTrackingYamlEventImplementation]
    properties: dict[str, AnalyzeTrackingYamlEventProperty]

    @property
    def context(self) -> str:
        return ",".join(
            [
                f"{implementation.path}:{implementation.line}@{implementation.function}"
                for implementation in self.implementations
            ]
        )

    @property
    def tags(self) -> list[str]:
        return list(
            set(
                [
                    f"destination:{implementation.destination}"
                    for implementation in self.implementations
                    if implementation.destination
                ]
                # TODO: add more tags
            )
        )


class AnalyzeTrackingYaml(BaseModel):
    version: int
    source: AnalyzeTrackingYamlSource
    events: dict[str, AnalyzeTrackingYamlEvent]

    def get_event_by_name(self, name: str) -> Optional[AnalyzeTrackingYamlEvent]:
        return self.events.get(name)


def parse_analyze_tracking_yaml(output_path: str) -> AnalyzeTrackingYaml:
    import yaml

    with open(output_path, "r") as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError(f"No data found in {output_path}")

    return AnalyzeTrackingYaml.model_validate(data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("output_path", type=str)
    args = parser.parse_args()

    output = parse_analyze_tracking_yaml(args.output_path)
    print(output.model_dump_json(indent=2))
    print(output.get_event_by_name("sign_up"))
