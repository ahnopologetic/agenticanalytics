from typing import Any, Optional
import uuid
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions.session import Session
from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.genai import types as adk_types
from structlog import get_logger
from config import config

from agents.agent import root_agent

logger = get_logger()


class MainAgentTaskManager:
    def __init__(self, agent: Agent, app_name: str):
        self.agent = agent
        self.session_service = (
            InMemorySessionService()
            if config.env == "dev"
            else DatabaseSessionService(db_url=config.db_url)
        )
        self.artifact_service = (
            InMemoryArtifactService()
            if config.env == "dev"
            else GcsArtifactService(bucket_name="agenticanalytics")
        )
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
            app_name=self.app_name, user_id=user_id, session_id=session_id
        )
        if not session:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
                state={
                    "status": "not_started",
                    "user_id": user_id,
                    "session_id": session_id,
                    **context,
                },
            )
            session_id = session.id

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
        logger.info("Running agent", user_id=user_id, session_id=session_id)
        logger.info("Request content", request_content=request_content)
        logger.info("Session", session=session)
        logger.info("Events async", events_async=events_async)

        raw_events = []

        final_message = None

        # Process events
        async for event in events_async:
            raw_events.append(event.model_dump(exclude_none=True))
            if event.is_final_response():
                if not event.content:
                    continue
                if not event.content.parts or not event.content.parts[0].text:
                    continue
                final_message = event.content.parts[0].text
                logger.info(
                    "final message", session_id=session.id, final_message=final_message
                )
                try:
                    await self.session_service.append_event(session, event)
                except ValueError as e:
                    logger.error("Error appending event", error=e)
                    continue

        return {
            "message": final_message,
            "status": "success",
            "data": {
                "raw_events": raw_events,
            },
        }

    async def get_session(self, session_id: str, user_id: str):
        return await self.runner.session_service.get_session(
            app_name=self.app_name, user_id=user_id, session_id=session_id
        )

    async def list_sessions(self, user_id: str):
        return await self.runner.session_service.list_sessions(
            app_name=self.app_name, user_id=user_id
        )

    async def create_session(
        self, context: dict[str, Any], session_id: Optional[str] = None
    ) -> Session:
        return await self.runner.session_service.create_session(
            app_name=self.app_name,
            user_id=context.get("user_id", "default_user_id"),
            session_id=session_id,
            state={
                "status": {},
                "user_id": context.get("user_id", "default_user_id"),
                "session_id": session_id,
            },
        )


agentic_analytics_task_manager = MainAgentTaskManager(root_agent, "agentic_analytics")
