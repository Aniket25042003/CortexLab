"""
Project Model

Represents a research project containing conversations, artifacts, and experiments.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.agent_run import AgentRun
    from app.models.artifact import Artifact
    from app.models.source import Source
    from app.models.experiment_upload import ExperimentUpload


class Project(Base):
    """Research project model."""
    
    __tablename__ = "projects"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    domain_tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="discovery"  # discovery, deep_dive, paper_drafting, completed
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    sources: Mapped[list["Source"]] = relationship(
        "Source",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    experiment_uploads: Mapped[list["ExperimentUpload"]] = relationship(
        "ExperimentUpload",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Project {self.title}>"
