"""
Projects API Routes

CRUD operations for research projects.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from datetime import datetime
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User, Project, Artifact, Source, ExperimentUpload, Conversation, AgentRun
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDetailResponse,
)

router = APIRouter()


import asyncio
from app.core.tasks import run_discovery_agent

@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new research project and start discovery agent."""
    project = Project(
        title=project_data.title,
        description=project_data.description,
        user_id=current_user.id,
        status="discovery",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(project)
    await db.flush()
    
    # Create initial conversation
    conversation = Conversation(project_id=project.id)
    db.add(conversation)
    
    # Auto-trigger discovery run
    query = project_data.description or project_data.title
    
    run = AgentRun(
        project_id=project.id,
        run_type="discovery",
        status="pending",  # Start as pending
        config={"query": query},
        started_at=datetime.utcnow(),
    )
    db.add(run)
    await db.commit()
    await db.refresh(project)
    
    # Trigger background agent execution
    asyncio.create_task(run_discovery_agent(run.id, project.id, query))
    
    return ProjectResponse.model_validate(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all projects for the current user."""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
    )
    projects = result.scalars().all()
    
    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(p) for p in projects],
        total=len(projects)
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a project by ID with counts."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get counts
    artifact_count = await db.scalar(
        select(func.count(Artifact.id)).where(Artifact.project_id == project_id)
    )
    source_count = await db.scalar(
        select(func.count(Source.id)).where(Source.project_id == project_id)
    )
    experiment_count = await db.scalar(
        select(func.count(ExperimentUpload.id)).where(ExperimentUpload.project_id == project_id)
    )
    
    return ProjectDetailResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        domain_tags=project.domain_tags,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        artifact_count=artifact_count or 0,
        source_count=source_count or 0,
        experiment_count=experiment_count or 0,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a project."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields if provided
    if project_data.title is not None:
        project.title = project_data.title
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.domain_tags is not None:
        project.domain_tags = {"tags": project_data.domain_tags}
    if project_data.status is not None:
        project.status = project_data.status
    
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project and all its related data."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    
    return {"message": "Project deleted successfully"}
