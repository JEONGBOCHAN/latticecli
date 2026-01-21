"""Domain layer - Core business entities and rules.

This is the innermost layer of Clean Architecture.
No external dependencies allowed - pure Python only.
"""

from claude_clone.domain.entities.run import Run, RunStatus
from claude_clone.domain.entities.approval import Approval, ApprovalStatus, ApprovalType
from claude_clone.domain.entities.event import Event, EventType
from claude_clone.domain.entities.task import Task, TaskStatus
from claude_clone.domain.exceptions import (
    DomainError,
    InvalidStateError,
    NotFoundError,
    AlreadyExistsError,
)

__all__ = [
    # Entities
    "Run",
    "RunStatus",
    "Approval",
    "ApprovalStatus",
    "ApprovalType",
    "Event",
    "EventType",
    "Task",
    "TaskStatus",
    # Exceptions
    "DomainError",
    "InvalidStateError",
    "NotFoundError",
    "AlreadyExistsError",
]
