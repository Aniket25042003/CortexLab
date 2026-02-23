"""
Agent Runs API Routes

Agent workflow execution and streaming.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_db
from app.core.streaming import create_sse_response, format_sse_event
from app.dependencies import get_current_user
from app.models import User, Project, AgentRun, RunEvent
from app.schemas import (
    DiscoveryRunRequest,
    DeepDiveRunRequest,
    PaperRunRequest,
    AgentRunResponse,
    AgentRunDetailResponse,
    AgentRunListResponse,
    RunEventResponse,
)

router = APIRouter()


@router.post("/projects/{project_id}/runs/discovery", response_model=AgentRunResponse)
async def start_discovery_run(
    project_id: str,
    request: DiscoveryRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a research discovery agent run.
    
    Analyzes the research domain to find trends, gaps, and opportunities.
    """
    # Verify project ownership
    project_result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create agent run
    run = AgentRun(
        project_id=project_id,
        run_type="discovery",
        status="pending",
        config={"query": request.query},
        started_at=datetime.utcnow(),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Trigger background execution
    from app.core.tasks import run_discovery_agent
    asyncio.create_task(run_discovery_agent(run.id, project.id, request.query))
    
    return AgentRunResponse.model_validate(run)


import asyncio
from app.core.tasks import run_deep_dive_agent, run_paper_agent

@router.post("/projects/{project_id}/runs/deep-dive", response_model=AgentRunResponse)
async def start_deep_dive_run(
    project_id: str,
    request: DeepDiveRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a deep dive agent run.
    
    Provides detailed experiment recommendations for a chosen research direction.
    """
    # Verify project ownership
    project_result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create agent run
    run = AgentRun(
        project_id=project_id,
        run_type="deep_dive",
        status="pending",
        config={
            "direction_id": request.direction_id,
            "direction_summary": request.direction_summary,
        },
        started_at=datetime.utcnow(),
    )
    db.add(run)
    
    # Update project status
    project.status = "deep_dive"
    
    await db.commit()
    await db.refresh(run)

    # Trigger background execution
    # Construct a direction object from request (the agent will fetch details if needed)
    direction = {
        "id": request.direction_id,
        "title": request.direction_summary,
        "description": request.direction_summary,
    }
    asyncio.create_task(run_deep_dive_agent(run.id, project.id, direction))
    
    return AgentRunResponse.model_validate(run)


@router.post("/projects/{project_id}/runs/paper", response_model=AgentRunResponse)
async def start_paper_run(
    project_id: str,
    request: PaperRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a paper drafting agent run.
    
    Generates a research paper draft from experiment results.
    """
    # Verify project ownership
    project_result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Create agent run
    run = AgentRun(
        project_id=project_id,
        run_type="paper",
        status="pending",
        config={"experiment_ids": request.include_experiments},
        started_at=datetime.utcnow(),
    )
    db.add(run)
    
    # Update project status
    project.status = "paper_drafting"
    
    await db.commit()
    await db.refresh(run)
    
    # Trigger background execution
    asyncio.create_task(run_paper_agent(run.id, project.id, {}, []))  # TODO: Pass actual direction and experiment data
    
    return AgentRunResponse.model_validate(run)



@router.get("/runs/{run_id}", response_model=AgentRunDetailResponse)
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details of an agent run including all events."""
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.id == run_id)
        .options(selectinload(AgentRun.events))
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Verify ownership through project
    project_result = await db.execute(
        select(Project)
        .where(Project.id == run.project_id, Project.user_id == current_user.id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Run not found")
    
    return AgentRunDetailResponse(
        id=run.id,
        project_id=run.project_id,
        run_type=run.run_type,
        status=run.status,
        config=run.config,
        result=run.result,
        error_message=run.error_message,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
        events=[RunEventResponse.model_validate(e) for e in run.events]
    )


@router.get("/runs/{run_id}/events")
async def stream_run_events(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream run events via Server-Sent Events (SSE).
    
    Opens a persistent connection to receive real-time agent progress updates.
    """
    # Verify run exists and user owns it
    result = await db.execute(
        select(AgentRun).where(AgentRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    project_result = await db.execute(
        select(Project)
        .where(Project.id == run.project_id, Project.user_id == current_user.id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Run not found")
    
    async def event_generator():
        """Generate SSE events for the run."""
        # TODO: Implement actual event streaming from agent execution
        # For now, yield existing events
        events_result = await db.execute(
            select(RunEvent)
            .where(RunEvent.run_id == run_id)
            .order_by(RunEvent.created_at)
        )
        events = events_result.scalars().all()
        
        for event in events:
            yield format_sse_event(event.event_type, {
                "id": event.id,
                "payload": event.payload,
                "created_at": event.created_at.isoformat()
            })
        
        # If run is complete, send completion event
        if run.status in ["completed", "failed"]:
            yield format_sse_event("run_complete", {
                "status": run.status,
                "result": run.result,
            })
    
    return create_sse_response(event_generator())


@router.get("/projects/{project_id}/runs", response_model=AgentRunListResponse)
async def list_runs(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all runs for a project."""
    # Verify project ownership
    project_result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.project_id == project_id)
        .order_by(AgentRun.created_at.desc())
    )
    runs = result.scalars().all()
    
    return AgentRunListResponse(
        runs=[AgentRunResponse.model_validate(r) for r in runs],
        total=len(runs)
    )
