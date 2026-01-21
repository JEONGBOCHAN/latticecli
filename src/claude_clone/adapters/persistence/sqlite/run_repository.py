"""SQLite implementation of RunRepository (stub for Phase 7)."""

from typing import Optional

from claude_clone.domain.entities.run import Run, RunStatus
from claude_clone.application.interfaces.run_repository import RunRepository


class SqliteRunRepository(RunRepository):
    """SQLite implementation of RunRepository.

    TODO: Implement in Phase 7
    """

    def __init__(self, db_path: str = "ops_board.db") -> None:
        self.db_path = db_path
        raise NotImplementedError("SqliteRunRepository will be implemented in Phase 7")

    def save(self, run: Run) -> None:
        raise NotImplementedError

    def find_by_id(self, run_id: str) -> Optional[Run]:
        raise NotImplementedError

    def find_active(self) -> list[Run]:
        raise NotImplementedError

    def find_by_status(self, status: RunStatus) -> list[Run]:
        raise NotImplementedError

    def list_recent(self, limit: int = 10) -> list[Run]:
        raise NotImplementedError

    def delete(self, run_id: str) -> bool:
        raise NotImplementedError
