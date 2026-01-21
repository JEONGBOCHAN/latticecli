"""Store: Abstract interface for persistent state storage.

The Store holds the "thick" state - events, approvals, diffs, artifacts.
This is an abstract base class; concrete implementations are in adapters/.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Store(ABC):
    """Abstract base class for state storage.

    Implementations:
    - InMemoryStore (for testing)
    - SqliteStore (for production)

    The Store is the "source of truth" for:
    - Events (immutable log)
    - Approvals (with diffs)
    - Artifacts (logs, reports)
    - Checkpoints (file snapshots)
    """

    # ==================== Runs ====================

    @abstractmethod
    def create_run(self, run_id: str, goal: str, repo_root: str) -> None:
        """Create a new run record."""
        ...

    @abstractmethod
    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        """Get run by ID."""
        ...

    @abstractmethod
    def update_run_status(self, run_id: str, status: str) -> None:
        """Update run status (running, completed, failed, cancelled)."""
        ...

    @abstractmethod
    def list_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent runs."""
        ...

    # ==================== Events ====================

    @abstractmethod
    def emit_event(
        self, run_id: str, event_type: str, data: Optional[dict[str, Any]] = None
    ) -> int:
        """Emit an event and return event_id."""
        ...

    @abstractmethod
    def get_events(
        self,
        run_id: str,
        since_event_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get events for a run, optionally since a cursor."""
        ...

    # ==================== Approvals ====================

    @abstractmethod
    def create_approval(
        self,
        run_id: str,
        approval_type: str,
        target: str,
        diff_content: Optional[str] = None,
        requester_worker_id: Optional[str] = None,
        requester_task_id: Optional[str] = None,
    ) -> str:
        """Create an approval request, return approval_id."""
        ...

    @abstractmethod
    def get_approval(self, approval_id: str) -> Optional[dict[str, Any]]:
        """Get approval by ID (includes diff if available)."""
        ...

    @abstractmethod
    def list_approvals(
        self, run_id: str, status: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """List approvals for a run, optionally filtered by status."""
        ...

    @abstractmethod
    def resolve_approval(
        self,
        approval_id: str,
        approved: bool,
        resolved_by: str = "user",
        comment: str = "",
    ) -> None:
        """Resolve an approval (approve or reject)."""
        ...

    # ==================== Artifacts ====================

    @abstractmethod
    def create_artifact(
        self,
        run_id: str,
        artifact_type: str,
        title: str,
        content: str,
        task_id: Optional[str] = None,
    ) -> str:
        """Create an artifact, return artifact_id."""
        ...

    @abstractmethod
    def get_artifact(self, artifact_id: str) -> Optional[dict[str, Any]]:
        """Get artifact by ID."""
        ...

    @abstractmethod
    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        """List artifacts for a run."""
        ...

    # ==================== Checkpoints ====================

    @abstractmethod
    def create_checkpoint(
        self,
        run_id: str,
        message: str,
        turn: int,
        snapshots: list[dict[str, str]],
    ) -> str:
        """Create a checkpoint with file snapshots, return checkpoint_id.

        snapshots: [{"file_path": "...", "content": "..."}]
        """
        ...

    @abstractmethod
    def get_checkpoint(self, checkpoint_id: str) -> Optional[dict[str, Any]]:
        """Get checkpoint by ID (includes snapshots)."""
        ...

    @abstractmethod
    def list_checkpoints(self, run_id: str) -> list[dict[str, Any]]:
        """List checkpoints for a run."""
        ...
