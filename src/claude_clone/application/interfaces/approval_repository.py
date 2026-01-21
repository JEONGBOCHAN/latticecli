"""ApprovalRepository interface - Abstract repository for Approval entities."""

from abc import ABC, abstractmethod
from typing import Optional

from claude_clone.domain.entities.approval import Approval, ApprovalStatus


class ApprovalRepository(ABC):
    """Abstract repository for Approval persistence.

    Implementations:
    - InMemoryApprovalRepository (testing)
    - SqliteApprovalRepository (production)
    """

    @abstractmethod
    def save(self, approval: Approval) -> None:
        """Save an approval (create or update)."""
        ...

    @abstractmethod
    def find_by_id(self, approval_id: str) -> Optional[Approval]:
        """Find an approval by ID. Returns None if not found."""
        ...

    @abstractmethod
    def find_by_run(self, run_id: str) -> list[Approval]:
        """Find all approvals for a run."""
        ...

    @abstractmethod
    def find_pending_by_run(self, run_id: str) -> list[Approval]:
        """Find pending approvals for a run."""
        ...

    @abstractmethod
    def find_by_status(
        self, run_id: str, status: ApprovalStatus
    ) -> list[Approval]:
        """Find approvals by run and status."""
        ...

    @abstractmethod
    def count_pending(self, run_id: str) -> int:
        """Count pending approvals for a run."""
        ...

    @abstractmethod
    def delete(self, approval_id: str) -> bool:
        """Delete an approval. Returns True if deleted, False if not found."""
        ...
