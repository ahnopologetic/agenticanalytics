from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from gotrue.types import User
from db_models import Repo, UserEvent, Plan
from server.routers.deps import get_current_user
from utils.db_session import get_db
from fastapi.responses import StreamingResponse
import io
import csv

router = APIRouter(tags=["repo"])


class RepoCreate(BaseModel):
    name: str
    description: str
    url: str
    created_at: datetime
    updated_at: datetime


class RepoUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RepoResponse(BaseModel):
    id: str | UUID
    user_id: str | UUID
    name: str
    label: str | None = None
    description: str | None = None
    url: str | None = None
    session_id: str | None = None
    created_at: datetime


class PlanCreate(BaseModel):
    repo_id: str
    name: str
    description: str = ""
    status: str = "active"
    version: str = "1.0"
    import_source: str = ""


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    import_source: Optional[str] = None


class PlanResponse(BaseModel):
    id: str
    repo_id: str
    name: str
    description: str
    status: str
    version: str
    import_source: str
    created_at: datetime
    updated_at: datetime


class UserEventCreate(BaseModel):
    plan_id: str
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
    plan_id: str
    repo_id: str
    event_name: str
    context: str
    tags: list[str]
    file_path: str
    line_number: int
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
def create_repo(
    repo: RepoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db_repo = Repo(**repo.model_dump(), user_id=user.id)
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo


@router.get("/", response_model=List[RepoResponse])
def get_repos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repos = (
        db.query(Repo).filter(Repo.user_id == user.id).offset(skip).limit(limit).all()
    )
    return repos


@router.get("/{repo_id}", response_model=RepoResponse)
def get_repo(
    repo_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    repo = db.query(Repo).filter(Repo.id == repo_id, Repo.user_id == user.id).first()
    if repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")
    return repo


@router.put("/{repo_id}", response_model=RepoResponse)
def update_repo(
    repo_id: str,
    repo: RepoUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db_repo = db.query(Repo).filter(Repo.id == repo_id, Repo.user_id == user.id).first()
    if db_repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")

    for key, value in repo.model_dump(exclude_unset=True).items():
        setattr(db_repo, key, value)

    db.commit()
    db.refresh(db_repo)
    return db_repo


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repo(repo_id: str, db: Session = Depends(get_db)):
    db_repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if db_repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")

    db.delete(db_repo)
    db.commit()
    return None


@router.get("/repo/{repo_id}/plans", response_model=List[PlanResponse])
def list_plans(repo_id: str, db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(Plan.repo_id == repo_id).all()
    return [
        PlanResponse(
            id=str(p.id),
            repo_id=str(p.repo_id),
            name=p.name,
            description=p.description or "",
            status=p.status,
            version=p.version,
            import_source=p.import_source or "",
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in plans
    ]


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanResponse(
        id=str(plan.id),
        repo_id=str(plan.repo_id),
        name=plan.name,
        description=plan.description or "",
        status=plan.status,
        version=plan.version,
        import_source=plan.import_source or "",
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    db_plan = Plan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return PlanResponse(
        id=str(db_plan.id),
        repo_id=str(db_plan.repo_id),
        name=db_plan.name,
        description=db_plan.description or "",
        status=db_plan.status,
        version=db_plan.version,
        import_source=db_plan.import_source or "",
        created_at=db_plan.created_at,
        updated_at=db_plan.updated_at,
    )


@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: str, plan: PlanUpdate, db: Session = Depends(get_db)):
    db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for key, value in plan.model_dump(exclude_unset=True).items():
        setattr(db_plan, key, value)
    db.commit()
    db.refresh(db_plan)
    return PlanResponse(
        id=str(db_plan.id),
        repo_id=str(db_plan.repo_id),
        name=db_plan.name,
        description=db_plan.description or "",
        status=db_plan.status,
        version=db_plan.version,
        import_source=db_plan.import_source or "",
        created_at=db_plan.created_at,
        updated_at=db_plan.updated_at,
    )


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: str, db: Session = Depends(get_db)):
    db_plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(db_plan)
    db.commit()
    return None


@router.get("/plans/{plan_id}/events", response_model=List[UserEventResponse])
def list_events_for_plan(plan_id: str, db: Session = Depends(get_db)):
    events = db.query(UserEvent).filter(UserEvent.plan_id == plan_id).all()
    return [
        UserEventResponse(
            id=str(e.id),
            plan_id=str(e.plan_id),
            repo_id=str(e.repo_id),
            event_name=e.event_name,
            context=e.context or "",
            tags=e.tags or [],
            file_path=e.file_path or "",
            line_number=e.line_number or 0,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in events
    ]


@router.post(
    "/events", response_model=UserEventResponse, status_code=status.HTTP_201_CREATED
)
def create_event(event: UserEventCreate, db: Session = Depends(get_db)):
    db_event = UserEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return UserEventResponse(
        id=str(db_event.id),
        plan_id=str(db_event.plan_id),
        repo_id=str(db_event.repo_id),
        event_name=db_event.event_name,
        context=db_event.context or "",
        tags=db_event.tags or [],
        file_path=db_event.file_path or "",
        line_number=db_event.line_number or 0,
        created_at=db_event.created_at,
        updated_at=db_event.updated_at,
    )


@router.put("/events/{event_id}", response_model=UserEventResponse)
def update_event(event_id: str, event: UserEventUpdate, db: Session = Depends(get_db)):
    db_event = db.query(UserEvent).filter(UserEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event.model_dump(exclude_unset=True).items():
        setattr(db_event, key, value)
    db.commit()
    db.refresh(db_event)
    return UserEventResponse(
        id=str(db_event.id),
        plan_id=str(db_event.plan_id),
        repo_id=str(db_event.repo_id),
        event_name=db_event.event_name,
        context=db_event.context or "",
        tags=db_event.tags or [],
        file_path=db_event.file_path or "",
        line_number=db_event.line_number or 0,
        created_at=db_event.created_at,
        updated_at=db_event.updated_at,
    )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    db_event = db.query(UserEvent).filter(UserEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(db_event)
    db.commit()
    return None


@router.get("/plans/{plan_id}/events/export", response_class=StreamingResponse)
def export_events_for_plan(plan_id: str, db: Session = Depends(get_db)):
    events = db.query(UserEvent).filter(UserEvent.plan_id == plan_id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "plan_id",
            "repo_id",
            "event_name",
            "context",
            "tags",
            "file_path",
            "line_number",
            "created_at",
            "updated_at",
        ]
    )
    for e in events:
        writer.writerow(
            [
                str(e.id),
                str(e.plan_id),
                str(e.repo_id),
                e.event_name,
                e.context or "",
                ",".join(e.tags or []),
                e.file_path or "",
                e.line_number or 0,
                e.created_at.isoformat(),
                e.updated_at.isoformat(),
            ]
        )
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plan_events.csv"},
    )


@router.post("/plans/{plan_id}/events/import", response_model=List[UserEventResponse])
def import_events_for_plan(
    plan_id: str, db: Session = Depends(get_db), file: bytes = None
):
    # This expects a CSV file upload via form-data with key 'file'
    import fastapi
    from fastapi import UploadFile, File as FastAPIFile
    import csv
    from uuid import uuid4

    class DummyRequest:
        pass

    request = DummyRequest()
    request.file = file
    # In real FastAPI, use: file: UploadFile = FastAPIFile(...)
    # For now, this is a placeholder for the actual implementation
    # TODO: Implement real file upload handling
    return []
