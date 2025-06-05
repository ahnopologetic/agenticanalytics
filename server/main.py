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

Base.metadata.create_all(bind=engine)
