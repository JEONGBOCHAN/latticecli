"""Tests for Approval entity."""

import pytest

from claude_clone.domain.entities.approval import (
    Approval,
    ApprovalStatus,
    ApprovalType,
)
from claude_clone.domain.exceptions import InvalidStateError


class TestApprovalCreation:
    """Test Approval creation."""

    def test_create_file_edit_approval(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
            diff_content="- old\n+ new",
        )

        assert approval.run_id == "run-123"
        assert approval.type == ApprovalType.FILE_EDIT
        assert approval.target == "src/main.py"
        assert approval.diff_content == "- old\n+ new"
        assert approval.status == ApprovalStatus.PENDING
        assert approval.id.startswith("apr-")

    def test_create_bash_command_approval(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.BASH_COMMAND,
            target="npm install",
        )

        assert approval.type == ApprovalType.BASH_COMMAND
        assert approval.target == "npm install"

    def test_approval_id_is_unique(self):
        apr1 = Approval.create(
            run_id="run-1", approval_type=ApprovalType.FILE_EDIT, target="a.py"
        )
        apr2 = Approval.create(
            run_id="run-1", approval_type=ApprovalType.FILE_EDIT, target="b.py"
        )

        assert apr1.id != apr2.id


class TestApprovalResolution:
    """Test Approval resolution."""

    def test_approve_pending(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )

        approval.approve(resolved_by="user", comment="LGTM")

        assert approval.status == ApprovalStatus.APPROVED
        assert approval.resolved_by == "user"
        assert approval.comment == "LGTM"
        assert approval.resolved_at is not None

    def test_reject_pending(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )

        approval.reject(resolved_by="user", comment="Too risky")

        assert approval.status == ApprovalStatus.REJECTED
        assert approval.resolved_by == "user"
        assert approval.comment == "Too risky"

    def test_cannot_approve_already_approved(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )
        approval.approve()

        with pytest.raises(InvalidStateError):
            approval.approve()

    def test_cannot_reject_already_rejected(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )
        approval.reject()

        with pytest.raises(InvalidStateError):
            approval.reject()

    def test_cannot_approve_rejected(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )
        approval.reject()

        with pytest.raises(InvalidStateError):
            approval.approve()


class TestApprovalExpiration:
    """Test Approval expiration."""

    def test_expire_pending(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )

        approval.expire()

        assert approval.status == ApprovalStatus.EXPIRED

    def test_cannot_expire_approved(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )
        approval.approve()

        with pytest.raises(InvalidStateError):
            approval.expire()


class TestApprovalProperties:
    """Test Approval properties."""

    def test_is_pending(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )

        assert approval.is_pending is True
        assert approval.is_resolved is False
        assert approval.is_approved is False

    def test_is_approved(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )
        approval.approve()

        assert approval.is_pending is False
        assert approval.is_resolved is True
        assert approval.is_approved is True

    def test_is_resolved_when_rejected(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )
        approval.reject()

        assert approval.is_pending is False
        assert approval.is_resolved is True
        assert approval.is_approved is False


class TestApprovalRiskAssessment:
    """Test Approval risk assessment."""

    def test_file_edit_base_risk(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )

        assert approval.risk_score == 2  # Base risk for FILE_EDIT

    def test_file_delete_higher_risk(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_DELETE,
            target="src/main.py",
        )

        assert approval.risk_score == 4  # Higher risk for DELETE

    def test_dangerous_pattern_increases_risk(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.BASH_COMMAND,
            target="rm -rf /tmp/test",
        )

        # Base 3 (BASH) + 1 (rm) + 1 (-rf) = 5
        assert approval.risk_score >= 4

    def test_sensitive_path_increases_risk(self):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target=".env",
        )

        # Base 2 + 1 (.env) = 3
        assert approval.risk_score >= 3
        assert ".env" in approval.risk_reason
