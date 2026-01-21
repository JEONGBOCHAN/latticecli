"""Approval entity - Represents a pending approval request."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from claude_clone.domain.exceptions import InvalidStateError


class ApprovalStatus(Enum):
    """Possible states of an Approval."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalType(Enum):
    """Types of operations requiring approval."""

    FILE_EDIT = "file_edit"
    FILE_CREATE = "file_create"
    FILE_DELETE = "file_delete"
    BASH_COMMAND = "bash_command"
    GIT_PUSH = "git_push"


@dataclass
class Approval:
    """An Approval represents a request for user confirmation.

    Business rules:
    - Approvals start in PENDING status
    - Can only be resolved (approved/rejected) from PENDING
    - Once resolved, cannot change status
    - Expired approvals cannot be resolved
    """

    id: str
    run_id: str
    type: ApprovalType
    target: str  # file path or command
    status: ApprovalStatus = ApprovalStatus.PENDING
    diff_content: Optional[str] = None
    requester_worker_id: Optional[str] = None
    requester_task_id: Optional[str] = None
    risk_score: int = 1  # 1-5, higher = more risky
    risk_reason: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # "user" or "auto"
    comment: str = ""

    def approve(self, resolved_by: str = "user", comment: str = "") -> None:
        """Approve this request."""
        self._resolve(ApprovalStatus.APPROVED, resolved_by, comment)

    def reject(self, resolved_by: str = "user", comment: str = "") -> None:
        """Reject this request."""
        self._resolve(ApprovalStatus.REJECTED, resolved_by, comment)

    def expire(self) -> None:
        """Mark as expired (cannot be resolved anymore)."""
        if self.status != ApprovalStatus.PENDING:
            raise InvalidStateError(
                f"Cannot expire approval in {self.status.value} status"
            )
        self.status = ApprovalStatus.EXPIRED
        self.resolved_at = datetime.utcnow()

    def _resolve(
        self, new_status: ApprovalStatus, resolved_by: str, comment: str
    ) -> None:
        """Internal method to resolve the approval."""
        if self.status != ApprovalStatus.PENDING:
            raise InvalidStateError(
                f"Cannot resolve approval in {self.status.value} status"
            )
        if self.is_expired:
            raise InvalidStateError("Cannot resolve expired approval")

        self.status = new_status
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        self.comment = comment

    @property
    def is_pending(self) -> bool:
        """Check if approval is still pending."""
        return self.status == ApprovalStatus.PENDING

    @property
    def is_resolved(self) -> bool:
        """Check if approval has been resolved."""
        return self.status in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}

    @property
    def is_expired(self) -> bool:
        """Check if approval has expired."""
        if self.status == ApprovalStatus.EXPIRED:
            return True
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False

    @property
    def is_approved(self) -> bool:
        """Check if approval was approved."""
        return self.status == ApprovalStatus.APPROVED

    def assess_risk(self) -> tuple[int, str]:
        """Assess risk level based on approval type and target.

        Returns (score: 1-5, reason: str)
        """
        # Base risk by type
        risk_by_type = {
            ApprovalType.FILE_EDIT: 2,
            ApprovalType.FILE_CREATE: 2,
            ApprovalType.FILE_DELETE: 4,
            ApprovalType.BASH_COMMAND: 3,
            ApprovalType.GIT_PUSH: 4,
        }
        score = risk_by_type.get(self.type, 2)
        reasons = []

        # Adjust for dangerous patterns
        dangerous_patterns = ["rm ", "sudo", "DROP", "DELETE", "--force", "-rf"]
        for pattern in dangerous_patterns:
            if pattern in self.target:
                score = min(5, score + 1)
                reasons.append(f"contains '{pattern}'")

        # Adjust for sensitive paths
        sensitive_paths = [".env", "credentials", "secret", "password", ".git/"]
        for path in sensitive_paths:
            if path in self.target.lower():
                score = min(5, score + 1)
                reasons.append(f"touches sensitive path '{path}'")

        reason = ", ".join(reasons) if reasons else f"standard {self.type.value}"
        self.risk_score = score
        self.risk_reason = reason
        return score, reason

    @classmethod
    def create(
        cls,
        run_id: str,
        approval_type: ApprovalType,
        target: str,
        diff_content: Optional[str] = None,
        worker_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> "Approval":
        """Factory method to create a new Approval."""
        approval = cls(
            id=f"apr-{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            type=approval_type,
            target=target,
            diff_content=diff_content,
            requester_worker_id=worker_id,
            requester_task_id=task_id,
        )
        approval.assess_risk()
        return approval
