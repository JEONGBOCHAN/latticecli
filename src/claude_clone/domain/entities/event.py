"""Event entity - Represents an immutable event in the timeline."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EventType(Enum):
    """Types of events that can occur."""

    # Run lifecycle
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    RUN_CANCELLED = "run.cancelled"

    # Plan lifecycle
    PLAN_CREATED = "plan.created"
    PLAN_UPDATED = "plan.updated"
    PHASE_STARTED = "phase.started"
    PHASE_COMPLETED = "phase.completed"

    # Task lifecycle
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_BLOCKED = "task.blocked"

    # Tool usage
    TOOL_CALLED = "tool.called"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"

    # File operations
    FILE_READ = "file.read"
    FILE_CHANGED = "file.changed"
    FILE_CREATED = "file.created"
    FILE_DELETED = "file.deleted"

    # Approval lifecycle
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_EXPIRED = "approval.expired"

    # Checkpoint
    CHECKPOINT_CREATED = "checkpoint.created"
    CHECKPOINT_RESTORED = "checkpoint.restored"

    # Test
    TEST_STARTED = "test.started"
    TEST_PASSED = "test.passed"
    TEST_FAILED = "test.failed"

    # Generic
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Event:
    """An immutable event in the agent timeline.

    Events are append-only and never modified after creation.
    They form the complete audit trail of what happened.
    """

    id: int  # Auto-incremented
    run_id: str
    type: EventType
    timestamp: datetime
    data: dict[str, Any] = field(default_factory=dict)

    def to_summary(self) -> str:
        """Generate a 1-line summary for ThinState.recent_events_digest."""
        # Format: "type target" or "type key=value"
        type_str = self.type.value.replace(".", " ")

        if "path" in self.data:
            return f"{type_str} {self.data['path']}"
        elif "target" in self.data:
            return f"{type_str} {self.data['target']}"
        elif "message" in self.data:
            msg = self.data["message"][:50]
            return f"{type_str}: {msg}"
        elif "tool" in self.data:
            return f"{type_str} {self.data['tool']}"
        else:
            return type_str

    @classmethod
    def create(
        cls,
        event_id: int,
        run_id: str,
        event_type: EventType,
        data: Optional[dict[str, Any]] = None,
    ) -> "Event":
        """Factory method to create a new Event."""
        return cls(
            id=event_id,
            run_id=run_id,
            type=event_type,
            timestamp=datetime.utcnow(),
            data=data or {},
        )

    # Convenience factory methods for common events

    @classmethod
    def run_started(cls, event_id: int, run_id: str, goal: str) -> "Event":
        """Create a run.started event."""
        return cls.create(
            event_id, run_id, EventType.RUN_STARTED, {"goal": goal}
        )

    @classmethod
    def tool_called(
        cls, event_id: int, run_id: str, tool: str, args: dict[str, Any]
    ) -> "Event":
        """Create a tool.called event."""
        return cls.create(
            event_id, run_id, EventType.TOOL_CALLED, {"tool": tool, "args": args}
        )

    @classmethod
    def file_changed(cls, event_id: int, run_id: str, path: str) -> "Event":
        """Create a file.changed event."""
        return cls.create(
            event_id, run_id, EventType.FILE_CHANGED, {"path": path}
        )

    @classmethod
    def approval_requested(
        cls, event_id: int, run_id: str, approval_id: str, target: str
    ) -> "Event":
        """Create an approval.requested event."""
        return cls.create(
            event_id,
            run_id,
            EventType.APPROVAL_REQUESTED,
            {"approval_id": approval_id, "target": target},
        )
