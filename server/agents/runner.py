from typing import Any, Optional
import uuid
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.genai import types as adk_types
from agents.agent import root_agent
from structlog import get_logger


logger = get_logger()


class RepoReaderTaskManager:
    def __init__(self, agent: Agent, app_name: str):
        self.agent = agent
        self.session_service = InMemorySessionService()
        self.artifact_service = InMemoryArtifactService()
        self.app_name = app_name
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
            artifact_service=self.artifact_service,
        )

    async def execute(
        self, message: str, context: dict[str, Any], session_id: Optional[str] = None
    ):
        user_id = context.get("user_id", "default_user_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {session_id}")

        session = await self.session_service.get_session(
            app_name="repo_reader", user_id=user_id, session_id=session_id
        )
        if not session:
            session = await self.session_service.create_session(
                app_name="repo_reader", user_id=user_id, session_id=session_id, state={}
            )
            logger.info(f"Created new session: {session_id}")

        # Create user message
        request_content = adk_types.Content(
            role="user", parts=[adk_types.Part(text=message)]
        )

        try:
            events_async = self.runner.run_async(
                user_id=user_id, session_id=session_id, new_message=request_content
            )
        except Exception as e:
            logger.error("Error running agent", error=e)
            return {
                "status": "error",
                "data": {},
            }

        raw_events = []

        final_message = None

        # Process events
        async for event in events_async:
            logger.debug("Event", raw_event=event.model_dump(exclude_none=True))
            raw_events.append(event.model_dump(exclude_none=True))
            if event.is_final_response():
                final_message = event.content.parts[0].text

        return {
            "message": final_message,
            "status": "success",
            "data": {
                "raw_events": raw_events,
            },
        }


repo_reader_task_manager = RepoReaderTaskManager(root_agent, "repo_reader")
