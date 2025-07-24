from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structlog import get_logger
from config import config
from supabase import Client, create_client
from db_models import Base
from db import engine

from routers.github import router as github_router
from routers.auth import router as auth_router
from routers.agent import router as agent_router
from routers.repo import router as repo_router
from routers.plans import router as plans_router
from routers.events import router as events_router

logger = get_logger()

supabase: Client = create_client(config.supabase_url, config.supabase_service_role_key)

app = FastAPI(root_path="/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agenticanalytics.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(github_router, prefix="/github")
app.include_router(auth_router, prefix="/auth")
app.include_router(agent_router, prefix="/agent")
app.include_router(repo_router, prefix="/repo")
app.include_router(plans_router, prefix="/plans")
app.include_router(events_router, prefix="/events")

Base.metadata.create_all(bind=engine)
