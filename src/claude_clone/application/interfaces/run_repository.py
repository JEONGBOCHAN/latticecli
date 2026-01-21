"""RunRepository interface - Abstract repository for Run entities."""

from abc import ABC, abstractmethod
from typing import Optional

from claude_clone.domain.entities.run import Run, RunStatus


class RunRepository(ABC):
    """Abstract repository for Run persistence.

    Implementations:
    - InMemoryRunRepository (testing)
    - SqliteRunRepository (production)
    """

    @abstractmethod
    def save(self, run: Run) -> None:
        """Save a run (create or update)."""
        ...

    @abstractmethod
    def find_by_id(self, run_id: str) -> Optional[Run]:
        """Find a run by ID. Returns None if not found."""
        ...

    @abstractmethod
    def find_active(self) -> list[Run]:
        """Find all active (non-terminal) runs."""
        ...

    @abstractmethod
    def find_by_status(self, status: RunStatus) -> list[Run]:
        """Find runs by status."""
        ...

    @abstractmethod
    def list_recent(self, limit: int = 10) -> list[Run]:
        """List recent runs, ordered by created_at desc."""
        ...

    @abstractmethod
    def delete(self, run_id: str) -> bool:
        """Delete a run. Returns True if deleted, False if not found."""
        ...
