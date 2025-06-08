from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db_models import Repo
from utils.db_session import get_db

router = APIRouter(prefix="/repo", tags=["repo"])


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
    id: int
    name: str
    description: str
    url: str
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
def create_repo(repo: RepoCreate, db: Session = Depends(get_db)):
    db_repo = Repo(**repo.dict())
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo


@router.get("/", response_model=List[RepoResponse])
def get_repos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repos = db.query(Repo).offset(skip).limit(limit).all()
    return repos


@router.get("/{repo_id}", response_model=RepoResponse)
def get_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")
    return repo


@router.put("/{repo_id}", response_model=RepoResponse)
def update_repo(repo_id: int, repo: RepoUpdate, db: Session = Depends(get_db)):
    db_repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if db_repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")

    for key, value in repo.dict(exclude_unset=True).items():
        setattr(db_repo, key, value)

    db.commit()
    db.refresh(db_repo)
    return db_repo


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repo(repo_id: int, db: Session = Depends(get_db)):
    db_repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if db_repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")

    db.delete(db_repo)
    db.commit()
    return None
