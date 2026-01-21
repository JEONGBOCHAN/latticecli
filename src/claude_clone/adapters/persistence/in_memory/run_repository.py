"""In-memory implementation of RunRepository for testing."""

from typing import Optional

from claude_clone.domain.entities.run import Run, RunStatus
from claude_clone.application.interfaces.run_repository import RunRepository


class InMemoryRunRepository(RunRepository):
    """In-memory implementation of RunRepository.

    Useful for:
    - Unit testing
    - Quick prototyping
    - Development without database
    """

    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}

    def save(self, run: Run) -> None:
        """Save a run (create or update)."""
        self._runs[run.id] = run

    def find_by_id(self, run_id: str) -> Optional[Run]:
        """Find a run by ID. Returns None if not found."""
        return self._runs.get(run_id)

    def find_active(self) -> list[Run]:
        """Find all active (non-terminal) runs."""
        return [run for run in self._runs.values() if run.is_active]

    def find_by_status(self, status: RunStatus) -> list[Run]:
        """Find runs by status."""
        return [run for run in self._runs.values() if run.status == status]

    def list_recent(self, limit: int = 10) -> list[Run]:
        """List recent runs, ordered by created_at desc."""
        runs = sorted(
            self._runs.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )
        return runs[:limit]

    def delete(self, run_id: str) -> bool:
        """Delete a run. Returns True if deleted, False if not found."""
        if run_id in self._runs:
            del self._runs[run_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all runs (for testing)."""
        self._runs.clear()

    def count(self) -> int:
        """Count total runs (for testing)."""
        return len(self._runs)
