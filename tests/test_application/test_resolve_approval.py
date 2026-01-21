"""Tests for ResolveApprovalUseCase."""

import pytest

from claude_clone.domain.entities.approval import (
    Approval,
    ApprovalType,
    ApprovalStatus,
)
from claude_clone.domain.entities.event import EventType
from claude_clone.domain.exceptions import NotFoundError
from claude_clone.application.use_cases.resolve_approval import (
    ResolveApprovalUseCase,
    ResolveApprovalRequest,
)
from claude_clone.adapters.persistence.in_memory import (
    InMemoryApprovalRepository,
    InMemoryEventRepository,
)
from claude_clone.adapters.messaging.event_bus import EventBus


@pytest.fixture
def approval_repository():
    return InMemoryApprovalRepository()


@pytest.fixture
def event_repository():
    return InMemoryEventRepository()


@pytest.fixture
def event_publisher(event_repository):
    return EventBus(event_repository=event_repository)


@pytest.fixture
def use_case(approval_repository, event_publisher):
    return ResolveApprovalUseCase(
        approval_repository=approval_repository,
        event_publisher=event_publisher,
    )


@pytest.fixture
def pending_approval(approval_repository):
    """Create and save a pending approval."""
    approval = Approval.create(
        run_id="run-123",
        approval_type=ApprovalType.FILE_EDIT,
        target="src/main.py",
        diff_content="- old\n+ new",
    )
    approval_repository.save(approval)
    return approval


class TestResolveApprovalUseCase:
    """Test ResolveApprovalUseCase."""

    def test_approve_success(
        self, use_case, approval_repository, pending_approval
    ):
        request = ResolveApprovalRequest(
            approval_id=pending_approval.id,
            approved=True,
            comment="LGTM",
        )

        response = use_case.execute(request)

        assert response.approval_id == pending_approval.id
        assert response.status == "approved"
        assert response.target == "src/main.py"

        # Verify saved
        approval = approval_repository.find_by_id(pending_approval.id)
        assert approval.status == ApprovalStatus.APPROVED
        assert approval.comment == "LGTM"

    def test_reject_success(
        self, use_case, approval_repository, pending_approval
    ):
        request = ResolveApprovalRequest(
            approval_id=pending_approval.id,
            approved=False,
            comment="Too risky",
        )

        response = use_case.execute(request)

        assert response.status == "rejected"

        approval = approval_repository.find_by_id(pending_approval.id)
        assert approval.status == ApprovalStatus.REJECTED

    def test_approve_emits_event(
        self, use_case, event_repository, pending_approval
    ):
        request = ResolveApprovalRequest(
            approval_id=pending_approval.id,
            approved=True,
        )

        use_case.execute(request)

        events = event_repository.find_by_run("run-123")
        assert len(events) == 1
        assert events[0].type == EventType.APPROVAL_APPROVED
        assert events[0].data["approval_id"] == pending_approval.id

    def test_reject_emits_event(
        self, use_case, event_repository, pending_approval
    ):
        request = ResolveApprovalRequest(
            approval_id=pending_approval.id,
            approved=False,
        )

        use_case.execute(request)

        events = event_repository.find_by_run("run-123")
        assert len(events) == 1
        assert events[0].type == EventType.APPROVAL_REJECTED

    def test_not_found_error(self, use_case):
        request = ResolveApprovalRequest(
            approval_id="nonexistent",
            approved=True,
        )

        with pytest.raises(NotFoundError) as exc_info:
            use_case.execute(request)

        assert exc_info.value.entity_type == "Approval"
        assert exc_info.value.entity_id == "nonexistent"

    def test_resolved_by_is_recorded(
        self, use_case, approval_repository, pending_approval
    ):
        request = ResolveApprovalRequest(
            approval_id=pending_approval.id,
            approved=True,
            resolved_by="admin",
        )

        use_case.execute(request)

        approval = approval_repository.find_by_id(pending_approval.id)
        assert approval.resolved_by == "admin"
