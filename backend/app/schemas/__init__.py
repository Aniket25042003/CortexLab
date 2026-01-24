"""Schemas Package - Pydantic Request/Response Models"""

from app.schemas.auth import (
    GoogleAuthRequest,
    UserResponse,
    AuthResponse,
    SessionValidation,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDetailResponse,
)
from app.schemas.run import (
    DiscoveryRunRequest,
    DeepDiveRunRequest,
    PaperRunRequest,
    RevisionRunRequest,
    RunEventResponse,
    AgentRunResponse,
    AgentRunDetailResponse,
    AgentRunListResponse,
)
from app.schemas.artifact import (
    ArtifactCreate,
    ArtifactUpdate,
    ArtifactReviseRequest,
    ArtifactResponse,
    ArtifactListResponse,
    SourceResponse,
    SourceListResponse,
    ExperimentUploadResponse,
    ExperimentListResponse,
)

__all__ = [
    # Auth
    "GoogleAuthRequest",
    "UserResponse",
    "AuthResponse",
    "SessionValidation",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ProjectDetailResponse",
    # Run
    "DiscoveryRunRequest",
    "DeepDiveRunRequest",
    "PaperRunRequest",
    "RevisionRunRequest",
    "RunEventResponse",
    "AgentRunResponse",
    "AgentRunDetailResponse",
    "AgentRunListResponse",
    # Artifact
    "ArtifactCreate",
    "ArtifactUpdate",
    "ArtifactReviseRequest",
    "ArtifactResponse",
    "ArtifactListResponse",
    "SourceResponse",
    "SourceListResponse",
    "ExperimentUploadResponse",
    "ExperimentListResponse",
]
