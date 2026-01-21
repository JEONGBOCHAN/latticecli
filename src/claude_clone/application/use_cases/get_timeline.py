"""GetTimelineUseCase - Get timeline of events for a run."""

from dataclasses import dataclass
from typing import Optional

from claude_clone.domain.entities.event import Event
from claude_clone.domain.exceptions import NotFoundError
from claude_clone.application.interfaces.run_repository import RunRepository
from claude_clone.application.interfaces.event_repository import EventRepository


@dataclass
class GetTimelineRequest:
    """Request to get timeline."""

    run_id: str
    since_event_id: Optional[int] = None
    limit: int = 100


@dataclass
class TimelineEvent:
    """A single event in the timeline response."""

    id: int
    type: str
    timestamp: str
    summary: str
    data: dict


@dataclass
class GetTimelineResponse:
    """Response containing timeline events."""

    run_id: str
    events: list[TimelineEvent]
    latest_event_id: Optional[int]
    has_more: bool


class GetTimelineUseCase:
    """Use case: Get timeline of events for a run.

    Steps:
    1. Validate run exists
    2. Query events since cursor
    3. Convert to response
    """

    def __init__(
        self,
        run_repository: RunRepository,
        event_repository: EventRepository,
    ):
        self.run_repository = run_repository
        self.event_repository = event_repository

    def execute(self, request: GetTimelineRequest) -> GetTimelineResponse:
        """Execute the use case."""
        # Validate run exists
        run = self.run_repository.find_by_id(request.run_id)
        if not run:
            raise NotFoundError("Run", request.run_id)

        # Query events
        events = self.event_repository.find_by_run(
            run_id=request.run_id,
            since_id=request.since_event_id,
            limit=request.limit + 1,  # +1 to check if there's more
        )

        # Check if there's more
        has_more = len(events) > request.limit
        if has_more:
            events = events[:request.limit]

        # Convert to response
        timeline_events = [
            TimelineEvent(
                id=e.id,
                type=e.type.value,
                timestamp=e.timestamp.isoformat(),
                summary=e.to_summary(),
                data=dict(e.data),
            )
            for e in events
        ]

        latest_id = events[-1].id if events else None

        return GetTimelineResponse(
            run_id=request.run_id,
            events=timeline_events,
            latest_event_id=latest_id,
            has_more=has_more,
        )
