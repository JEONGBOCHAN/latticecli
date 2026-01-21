"""ResolveApprovalUseCase - Approve or reject a pending approval."""

from dataclasses import dataclass

from claude_clone.domain.entities.event import EventType
from claude_clone.domain.exceptions import NotFoundError
from claude_clone.application.interfaces.approval_repository import ApprovalRepository
from claude_clone.application.interfaces.event_publisher import EventPublisher


@dataclass
class ResolveApprovalRequest:
    """Request to resolve an approval."""

    approval_id: str
    approved: bool
    comment: str = ""
    resolved_by: str = "user"


@dataclass
class ResolveApprovalResponse:
    """Response from resolving an approval."""

    approval_id: str
    status: str
    target: str


class ResolveApprovalUseCase:
    """Use case: Resolve (approve/reject) a pending approval.

    Steps:
    1. Find the approval
    2. Validate it's pending
    3. Resolve it
    4. Save to repository
    5. Publish event
    6. Return response
    """

    def __init__(
        self,
        approval_repository: ApprovalRepository,
        event_publisher: EventPublisher,
    ):
        self.approval_repository = approval_repository
        self.event_publisher = event_publisher

    def execute(self, request: ResolveApprovalRequest) -> ResolveApprovalResponse:
        """Execute the use case."""
        # Find approval
        approval = self.approval_repository.find_by_id(request.approval_id)
        if not approval:
            raise NotFoundError("Approval", request.approval_id)

        # Resolve it
        if request.approved:
            approval.approve(resolved_by=request.resolved_by, comment=request.comment)
            event_type = EventType.APPROVAL_APPROVED
        else:
            approval.reject(resolved_by=request.resolved_by, comment=request.comment)
            event_type = EventType.APPROVAL_REJECTED

        # Save
        self.approval_repository.save(approval)

        # Publish event
        self.event_publisher.publish(
            run_id=approval.run_id,
            event_type=event_type,
            data={
                "approval_id": approval.id,
                "target": approval.target,
                "resolved_by": request.resolved_by,
                "comment": request.comment,
            },
        )

        return ResolveApprovalResponse(
            approval_id=approval.id,
            status=approval.status.value,
            target=approval.target,
        )
