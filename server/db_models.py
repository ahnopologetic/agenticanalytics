from sqlalchemy import (
    JSON,
    Column,
    String,
    Text,
    Integer,
    ForeignKey,
    DateTime,
    ARRAY,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid
from datetime import datetime, timezone

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    avatar_url = Column(String)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    github_token = Column(String, nullable=True)

    repos = relationship("Repo", back_populates="user")


class Repo(Base):
    __tablename__ = "repos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    label = Column(String)
    description = Column(Text)
    url = Column(String)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("Profile", back_populates="repos")
    events = relationship("UserEvent", back_populates="repo")
    scan_jobs = relationship("ScanJob", back_populates="repo")
    plans = relationship("Plan", back_populates="repo")


class Plan(Base):
    __tablename__ = "plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="active")
    version = Column(String, default="1.0")
    import_source = Column(String)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    repo = relationship("Repo", back_populates="plans")
    events = relationship("UserEvent", back_populates="plan")


class UserEvent(Base):
    __tablename__ = "user_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"))
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"))
    event_name = Column(String, nullable=False)
    context = Column(Text)
    tags = Column(ARRAY(String))
    file_path = Column(String)
    line_number = Column(Integer)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    repo = relationship("Repo", back_populates="events")
    plan = relationship("Plan", back_populates="events")
    annotations = relationship("EventAnnotation", back_populates="event")


class ScanJob(Base):
    __tablename__ = "scan_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"))
    status = Column(String)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    repo = relationship("Repo", back_populates="scan_jobs")


class EventAnnotation(Base):
    __tablename__ = "event_annotations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_event_id = Column(
        UUID(as_uuid=True), ForeignKey("user_events.id", ondelete="CASCADE")
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    annotation = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    event = relationship("UserEvent", back_populates="annotations")


class AdkSession(Base):
    __tablename__ = "sessions"
    app_name = Column(String(128), primary_key=True)
    user_id = Column(String(128), primary_key=True)
    id = Column(String(128), primary_key=True, unique=True)
    state = Column(JSON)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    __table_args__ = (UniqueConstraint("id", name="sessions_id_key"),)
