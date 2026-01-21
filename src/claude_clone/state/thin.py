"""ThinState: Lightweight state for LLM consumption.

The LLM reads this every turn. Keep it small - no large data,
only references (IDs, cursors) to data in Store.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
import uuid

from claude_clone.state.types import (
    ApprovalsInfo,
    ArtifactIndex,
    EventCursor,
    FocusInfo,
    PermissionInfo,
    PhaseInfo,
    RepoInfo,
    ThinStateDict,
    WorkerInfo,
)

if TYPE_CHECKING:
    from claude_clone.state.store import Store


def _generate_run_id() -> str:
    """Generate a unique run ID."""
    return f"run-{uuid.uuid4().hex[:8]}"


@dataclass
class ThinState:
    """Thin state that LLM reads every turn.

    Design principles:
    - Small enough to include in every LLM call
    - No large text (diffs, logs) - only refs
    - Updated incrementally as agent runs
    """

    # Run metadata
    run_id: str = field(default_factory=_generate_run_id)
    turn: int = 0
    goal: str = ""
    repo: RepoInfo = field(
        default_factory=lambda: RepoInfo(root=".", worktree=None, branch=None)
    )

    # Constraints and permissions
    permission: PermissionInfo = field(
        default_factory=lambda: PermissionInfo(
            mode="default", policy_digest="write/edit/delete/bash require approval"
        )
    )
    constraints_digest: str = ""

    # Progress pointers
    phase: PhaseInfo = field(
        default_factory=lambda: PhaseInfo(current_phase_id=None, phase_status=None)
    )
    focus: FocusInfo = field(
        default_factory=lambda: FocusInfo(task_id=None, approval_id=None)
    )

    # Worker status
    workers: dict[str, WorkerInfo] = field(default_factory=dict)
    active_task_ids: list[str] = field(default_factory=list)

    # Approval queue
    approvals: ApprovalsInfo = field(
        default_factory=lambda: ApprovalsInfo(
            pending_ids=[], pending_count=0, focus_approval_id=None
        )
    )

    # Event cursor
    event_cursor: EventCursor = field(
        default_factory=lambda: EventCursor(last_event_id=None, last_ts=None)
    )
    recent_events_digest: list[str] = field(default_factory=list)

    # Artifacts index
    artifacts_index: list[ArtifactIndex] = field(default_factory=list)

    def increment_turn(self) -> None:
        """Increment turn counter (called on each user input)."""
        self.turn += 1

    def set_goal(self, goal: str) -> None:
        """Set the goal for this run."""
        self.goal = goal

    def add_pending_approval(self, approval_id: str) -> None:
        """Add an approval to the pending queue."""
        if approval_id not in self.approvals["pending_ids"]:
            self.approvals["pending_ids"].append(approval_id)
            self.approvals["pending_count"] = len(self.approvals["pending_ids"])
            # Set focus to the first pending approval
            if self.approvals["focus_approval_id"] is None:
                self.approvals["focus_approval_id"] = approval_id

    def remove_pending_approval(self, approval_id: str) -> None:
        """Remove an approval from the pending queue."""
        if approval_id in self.approvals["pending_ids"]:
            self.approvals["pending_ids"].remove(approval_id)
            self.approvals["pending_count"] = len(self.approvals["pending_ids"])
            # Update focus
            if self.approvals["focus_approval_id"] == approval_id:
                self.approvals["focus_approval_id"] = (
                    self.approvals["pending_ids"][0]
                    if self.approvals["pending_ids"]
                    else None
                )

    def add_event_digest(self, event_summary: str, max_events: int = 10) -> None:
        """Add an event summary to recent events (keep last N)."""
        self.recent_events_digest.append(event_summary)
        if len(self.recent_events_digest) > max_events:
            self.recent_events_digest = self.recent_events_digest[-max_events:]

    def update_event_cursor(self, event_id: int, ts: str) -> None:
        """Update the event cursor after fetching events."""
        self.event_cursor["last_event_id"] = event_id
        self.event_cursor["last_ts"] = ts

    def to_dict(self) -> ThinStateDict:
        """Convert to dictionary for serialization or LLM context."""
        return ThinStateDict(
            run_id=self.run_id,
            turn=self.turn,
            goal=self.goal,
            repo=self.repo,
            permission=self.permission,
            constraints_digest=self.constraints_digest,
            phase=self.phase,
            focus=self.focus,
            workers=self.workers,
            active_task_ids=self.active_task_ids,
            approvals=self.approvals,
            event_cursor=self.event_cursor,
            recent_events_digest=self.recent_events_digest,
            artifacts_index=self.artifacts_index,
        )

    def to_context_string(self) -> str:
        """Generate a concise context string for LLM system message."""
        lines = [
            f"Run: {self.run_id} | Turn: {self.turn}",
            f"Goal: {self.goal}" if self.goal else "Goal: (not set)",
        ]

        if self.approvals["pending_count"] > 0:
            lines.append(
                f"⚠ Pending approvals: {self.approvals['pending_count']} "
                f"(focus: {self.approvals['focus_approval_id']})"
            )

        if self.recent_events_digest:
            lines.append("Recent events:")
            for event in self.recent_events_digest[-5:]:
                lines.append(f"  - {event}")

        return "\n".join(lines)

    @classmethod
    def new_run(cls, goal: str = "", repo_root: str = ".") -> "ThinState":
        """Create a new ThinState for a fresh run."""
        state = cls()
        state.goal = goal
        state.repo = RepoInfo(root=repo_root, worktree=None, branch=None)
        return state
