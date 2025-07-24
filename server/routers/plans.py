from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi import HTTPException
from uuid import UUID
from gotrue.types import User

from routers.deps import get_current_user
from routers.repo import PlanCreate, PlanResponse, RepoResponse
from db_models import Plan, Repo
from utils.db_session import get_db

router = APIRouter(tags=["plans"])


class AddReposToPlan(BaseModel):
    repo_ids: list[str]


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan: PlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db_plan = Plan(**plan.model_dump(), user_id=user.id)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return PlanResponse(
        id=str(db_plan.id),
        name=db_plan.name,
        description=db_plan.description or "",
        status=db_plan.status,
        version=db_plan.version,
        import_source=db_plan.import_source or "",
        created_at=db_plan.created_at,
        updated_at=db_plan.updated_at,
        user_id=str(db_plan.user_id),
    )


@router.get("/")
def get_plans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plans = db.query(Plan).filter(Plan.user_id == user.id).all()
    return plans


@router.get("/{plan_id}")
def get_plan(
    plan_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/{plan_id}/events")
def get_plan_events(
    plan_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    events = []
    for repo in plan.repos:
        events.extend(repo.events)

    return events


@router.post("/{plan_id}/repos")
def add_repos_to_plan(
    plan_id: UUID,
    add_repos_to_plan: AddReposToPlan,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for repo_id in add_repos_to_plan.repo_ids:
        repo = db.query(Repo).filter(Repo.id == UUID(repo_id)).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repo not found")
        plan.repos.append(repo)
    db.commit()
    return [
        RepoResponse(
            id=str(repo.id),
            name=repo.name,
            description=repo.description or "",
            url=repo.url,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            user_id=str(repo.user_id),
            label=repo.label,
            session_id=repo.session_id,
        )
        for repo in plan.repos
    ]
