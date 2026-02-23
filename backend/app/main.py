"""
CortexLab Backend - FastAPI Application

Main entry point for the CortexLab Research Agent API.
"""

from contextlib import asynccontextmanager
import typing

# Monkeypatch removed as it is incompatible with current environment

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

from app.config import get_settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.api import auth, projects, runs, artifacts, experiments, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    settings = get_settings()

    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Initialize database
    await init_db()

    # ── Stale-run cleanup ──────────────────────────────────────────────────
    # Any run left in 'running' or 'pending' from a previously killed server
    # process can never complete — mark them all as 'failed' immediately so
    # the frontend doesn't poll forever.
    try:
        from sqlalchemy import update
        from datetime import datetime
        from app.core.database import AsyncSessionLocal
        from app.models import AgentRun

        async with AsyncSessionLocal() as db:
            stale_statuses = ["running", "pending"]
            result = await db.execute(
                update(AgentRun)
                .where(AgentRun.status.in_(stale_statuses))
                .values(
                    status="failed",
                    error_message="Server was restarted while this run was in progress. Please start a new run.",
                    finished_at=datetime.utcnow(),
                )
            )
            affected = result.rowcount
            if affected:
                import logging as _logging
                _logging.getLogger(__name__).warning(
                    f"[STARTUP] Marked {affected} stale run(s) as failed (server was restarted)."
                )
            await db.commit()
    except Exception as e:
        import logging as _logging
        _logging.getLogger(__name__).error(f"[STARTUP] Stale-run cleanup failed: {e}")
    # ───────────────────────────────────────────────────────────────────────

    yield

    # Shutdown
    # Add cleanup logic here if needed



def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="CortexLab API",
        description="AI-powered research assistant for discovering research gaps and generating papers",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Setup logging
    setup_logging("INFO")
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
    app.include_router(runs.router, prefix="/api", tags=["Agent Runs"])
    app.include_router(artifacts.router, prefix="/api", tags=["Artifacts"])
    app.include_router(experiments.router, prefix="/api", tags=["Experiments"])
    app.include_router(export.router, prefix="/api", tags=["Export"])
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
