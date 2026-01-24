"""
CortexLab Backend - FastAPI Application

Main entry point for the CortexLab Research Agent API.
"""

from contextlib import asynccontextmanager
import typing

# Monkeypatch ForwardRef._evaluate to handle the missing recursive_guard argument in Python 3.12+
# This fixes the compatibility issue between Pydantic V1 (used by LangChain) and Python 3.12
try:
    if hasattr(typing.ForwardRef, "_evaluate"):
        _original_evaluate = typing.ForwardRef._evaluate
        def _new_evaluate(self, globalns, localns, type_params=None, *, recursive_guard=None):
            if recursive_guard is None:
                recursive_guard = frozenset()
            
            # Handle Pydantic V1 call where 3rd arg (type_params) is actually the recursive_guard set
            if isinstance(type_params, set):
                recursive_guard = type_params
                type_params = None
                
            return _original_evaluate(self, globalns, localns, type_params, recursive_guard=recursive_guard)
        typing.ForwardRef._evaluate = _new_evaluate
except Exception as e:
    print(f"Warning: Failed to patch ForwardRef._evaluate: {e}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

from app.config import get_settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.api import auth, projects, conversations, runs, artifacts, experiments, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    settings = get_settings()
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Initialize database
    await init_db()
    
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
    app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
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
