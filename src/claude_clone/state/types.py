"""Type definitions for agent state.

These TypedDict classes define the shape of the thin state
that the LLM reads every turn.
"""

from typing import Optional, TypedDict


class RepoInfo(TypedDict):
    """Repository context information."""

    root: str
    worktree: Optional[str]
    branch: Optional[str]


class PermissionInfo(TypedDict):
    """Permission mode and policy summary."""

    mode: str  # "default" | "plan" | "accept_edits" | "bypass"
    policy_digest: str  # e.g., "write/edit/delete/bash require approval"


class PhaseInfo(TypedDict):
    """Current execution phase."""

    current_phase_id: Optional[str]
    phase_status: Optional[str]  # "pending" | "in_progress" | "completed"


class FocusInfo(TypedDict):
    """Current focus pointers."""

    task_id: Optional[str]
    approval_id: Optional[str]


class WorkerInfo(TypedDict):
    """Worker status summary (1-liner)."""

    status: str  # "idle" | "working" | "blocked" | "waiting_approval"
    task_id: Optional[str]
    summary_1liner: str  # e.g., "searching auth flow", "waiting approval apr-123"


class ApprovalsInfo(TypedDict):
    """Approval queue summary."""

    pending_ids: list[str]
    pending_count: int
    focus_approval_id: Optional[str]


class EventCursor(TypedDict):
    """Cursor for incremental event fetching."""

    last_event_id: Optional[int]
    last_ts: Optional[str]


class ArtifactIndex(TypedDict):
    """Artifact index entry (not the content itself)."""

    id: str
    type: str  # "patch" | "report" | "test_log" | "build_log"
    title: str
    ts: str


class ThinStateDict(TypedDict):
    """Full thin state structure as TypedDict.

    This is what the LLM sees every turn.
    Large data (diffs, logs) are stored in Store and referenced by ID.
    """

    # Run metadata
    run_id: str
    turn: int
    goal: str
    repo: RepoInfo

    # Constraints and permissions
    permission: PermissionInfo
    constraints_digest: str

    # Progress pointers
    phase: PhaseInfo
    focus: FocusInfo

    # Worker status (summary only)
    workers: dict[str, WorkerInfo]
    active_task_ids: list[str]

    # Approval queue (summary only)
    approvals: ApprovalsInfo

    # Event cursor
    event_cursor: EventCursor
    recent_events_digest: list[str]

    # Artifacts index
    artifacts_index: list[ArtifactIndex]
