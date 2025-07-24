from datetime import datetime
from fastapi import APIRouter, HTTPException
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends

from db_models import UserEvent
from utils.db_session import get_db


router = APIRouter(tags=["events"])


class UserEventCreate(BaseModel):
    repo_id: str
    event_name: str
    context: str = ""
    tags: list[str] = []
    file_path: str = ""
    line_number: int = 0


class UserEventUpdate(BaseModel):
    event_name: str | None = None
    context: str | None = None
    tags: list[str] | None = None
    file_path: str | None = None
    line_number: int | None = None


class UserEventResponse(BaseModel):
    id: str
    plan_id: str | UUID
    repo_id: str | UUID
    event_name: str
    context: str
    tags: list[str]
    file_path: str
    line_number: int
    created_at: datetime
    updated_at: datetime


@router.get("/")
async def get_events(db: Session = Depends(get_db)):
    events = db.query(UserEvent).all()
    return events


@router.get("/{event_id}")
async def get_event(event_id: UUID, db: Session = Depends(get_db)):
    event = db.query(UserEvent).filter(UserEvent.id == event_id).first()
    return event


@router.post("/")
async def create_event(event: UserEventCreate, db: Session = Depends(get_db)):
    db_event = UserEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.put("/{event_id}")
async def update_event(
    event_id: UUID, event: UserEventUpdate, db: Session = Depends(get_db)
):
    db_event = db.query(UserEvent).filter(UserEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    db_event.update(event.model_dump())
    db.commit()
    db.refresh(db_event)
    return db_event
