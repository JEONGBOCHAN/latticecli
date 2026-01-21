"""Run entity - Represents a single agent execution session."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from claude_clone.domain.exceptions import InvalidStateError


class RunStatus(Enum):
    """Possible states of a Run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Run:
    """A Run represents a single agent execution session.

    Business rules:
    - A run starts in PENDING status
    - Can only transition to RUNNING from PENDING
    - Can only complete/fail/cancel from RUNNING
    - Once completed/failed/cancelled, cannot change status
    """

    id: str
    goal: str
    status: RunStatus = RunStatus.PENDING
    repo_root: str = "."
    branch: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Valid state transitions
    _VALID_TRANSITIONS: dict[RunStatus, set[RunStatus]] = field(
        default_factory=lambda: {
            RunStatus.PENDING: {RunStatus.RUNNING, RunStatus.CANCELLED},
            RunStatus.RUNNING: {
                RunStatus.COMPLETED,
                RunStatus.FAILED,
                RunStatus.CANCELLED,
            },
            RunStatus.COMPLETED: set(),
            RunStatus.FAILED: set(),
            RunStatus.CANCELLED: set(),
        },
        repr=False,
    )

    def _can_transition_to(self, new_status: RunStatus) -> bool:
        """Check if transition to new_status is valid."""
        return new_status in self._VALID_TRANSITIONS[self.status]

    def _transition_to(self, new_status: RunStatus) -> None:
        """Transition to new status if valid."""
        if not self._can_transition_to(new_status):
            raise InvalidStateError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def start(self) -> None:
        """Start the run (PENDING -> RUNNING)."""
        self._transition_to(RunStatus.RUNNING)

    def complete(self) -> None:
        """Mark run as completed (RUNNING -> COMPLETED)."""
        self._transition_to(RunStatus.COMPLETED)

    def fail(self) -> None:
        """Mark run as failed (RUNNING -> FAILED)."""
        self._transition_to(RunStatus.FAILED)

    def cancel(self) -> None:
        """Cancel the run (PENDING/RUNNING -> CANCELLED)."""
        self._transition_to(RunStatus.CANCELLED)

    @property
    def is_terminal(self) -> bool:
        """Check if run is in a terminal state."""
        return self.status in {
            RunStatus.COMPLETED,
            RunStatus.FAILED,
            RunStatus.CANCELLED,
        }

    @property
    def is_active(self) -> bool:
        """Check if run is active (pending or running)."""
        return self.status in {RunStatus.PENDING, RunStatus.RUNNING}

    @classmethod
    def create(cls, goal: str, repo_root: str = ".") -> "Run":
        """Factory method to create a new Run."""
        return cls(
            id=f"run-{uuid.uuid4().hex[:8]}",
            goal=goal,
            repo_root=repo_root,
        )
