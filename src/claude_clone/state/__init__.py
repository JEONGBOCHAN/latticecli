"""State management for the coding agent.

Two-layer state design:
- ThinState: Lightweight state for LLM (refs only, no large data)
- Store: Persistent storage for events, approvals, diffs, artifacts
"""

from claude_clone.state.thin import ThinState
from claude_clone.state.store import Store
from claude_clone.state.types import (
    ApprovalsInfo,
    ArtifactIndex,
    EventCursor,
    FocusInfo,
    PermissionInfo,
    PhaseInfo,
    RepoInfo,
    WorkerInfo,
)

__all__ = [
    "ThinState",
    "Store",
    "ApprovalsInfo",
    "ArtifactIndex",
    "EventCursor",
    "FocusInfo",
    "PermissionInfo",
    "PhaseInfo",
    "RepoInfo",
    "WorkerInfo",
]
