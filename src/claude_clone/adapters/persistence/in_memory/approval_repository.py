"""In-memory implementation of ApprovalRepository for testing."""

from typing import Optional

from claude_clone.domain.entities.approval import Approval, ApprovalStatus
from claude_clone.application.interfaces.approval_repository import ApprovalRepository


class InMemoryApprovalRepository(ApprovalRepository):
    """In-memory implementation of ApprovalRepository.

    Useful for:
    - Unit testing
    - Quick prototyping
    - Development without database
    """

    def __init__(self) -> None:
        self._approvals: dict[str, Approval] = {}

    def save(self, approval: Approval) -> None:
        """Save an approval (create or update)."""
        self._approvals[approval.id] = approval

    def find_by_id(self, approval_id: str) -> Optional[Approval]:
        """Find an approval by ID. Returns None if not found."""
        return self._approvals.get(approval_id)

    def find_by_run(self, run_id: str) -> list[Approval]:
        """Find all approvals for a run."""
        return [a for a in self._approvals.values() if a.run_id == run_id]

    def find_pending_by_run(self, run_id: str) -> list[Approval]:
        """Find pending approvals for a run."""
        return [
            a
            for a in self._approvals.values()
            if a.run_id == run_id and a.status == ApprovalStatus.PENDING
        ]

    def find_by_status(
        self, run_id: str, status: ApprovalStatus
    ) -> list[Approval]:
        """Find approvals by run and status."""
        return [
            a
            for a in self._approvals.values()
            if a.run_id == run_id and a.status == status
        ]

    def count_pending(self, run_id: str) -> int:
        """Count pending approvals for a run."""
        return len(self.find_pending_by_run(run_id))

    def delete(self, approval_id: str) -> bool:
        """Delete an approval. Returns True if deleted, False if not found."""
        if approval_id in self._approvals:
            del self._approvals[approval_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all approvals (for testing)."""
        self._approvals.clear()

    def count(self) -> int:
        """Count total approvals (for testing)."""
        return len(self._approvals)
