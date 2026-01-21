"""Task entity - Represents a unit of work within a run."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from claude_clone.domain.exceptions import InvalidStateError


class TaskStatus(Enum):
    """Possible states of a Task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"  # Waiting for approval or dependency


@dataclass
class Task:
    """A Task represents a unit of work assigned to a worker.

    Business rules:
    - Tasks start in PENDING status
    - Can be assigned (-> IN_PROGRESS) only from PENDING
    - Can be blocked (-> BLOCKED) from IN_PROGRESS
    - Can be unblocked (-> IN_PROGRESS) from BLOCKED
    - Can be completed/failed from IN_PROGRESS
    """

    id: str
    run_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    owner_worker_id: Optional[str] = None
    priority: int = 0  # Higher = more important
    input_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def assign(self, worker_id: str) -> None:
        """Assign task to a worker (PENDING -> IN_PROGRESS)."""
        if self.status != TaskStatus.PENDING:
            raise InvalidStateError(
                f"Cannot assign task in {self.status.value} status"
            )
        self.owner_worker_id = worker_id
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def block(self, reason: str = "") -> None:
        """Block task (IN_PROGRESS -> BLOCKED)."""
        if self.status != TaskStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Cannot block task in {self.status.value} status"
            )
        self.status = TaskStatus.BLOCKED
        if reason:
            self.error_message = reason
        self.updated_at = datetime.utcnow()

    def unblock(self) -> None:
        """Unblock task (BLOCKED -> IN_PROGRESS)."""
        if self.status != TaskStatus.BLOCKED:
            raise InvalidStateError(
                f"Cannot unblock task in {self.status.value} status"
            )
        self.status = TaskStatus.IN_PROGRESS
        self.error_message = None
        self.updated_at = datetime.utcnow()

    def complete(self, output_refs: Optional[list[str]] = None) -> None:
        """Mark task as completed (IN_PROGRESS -> COMPLETED)."""
        if self.status != TaskStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Cannot complete task in {self.status.value} status"
            )
        self.status = TaskStatus.COMPLETED
        if output_refs:
            self.output_refs.extend(output_refs)
        self.updated_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """Mark task as failed (IN_PROGRESS -> FAILED)."""
        if self.status != TaskStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Cannot fail task in {self.status.value} status"
            )
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        """Check if task is active (pending, in_progress, or blocked)."""
        return self.status in {
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
        }

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}

    @classmethod
    def create(
        cls,
        run_id: str,
        title: str,
        description: str = "",
        priority: int = 0,
    ) -> "Task":
        """Factory method to create a new Task."""
        return cls(
            id=f"task-{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            title=title,
            description=description,
            priority=priority,
        )
