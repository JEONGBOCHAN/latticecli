"""Tests for GetTimelineUseCase."""

import pytest

from claude_clone.domain.entities.run import Run
from claude_clone.domain.entities.event import Event, EventType
from claude_clone.domain.exceptions import NotFoundError
from claude_clone.application.use_cases.get_timeline import (
    GetTimelineUseCase,
    GetTimelineRequest,
)
from claude_clone.adapters.persistence.in_memory import (
    InMemoryRunRepository,
    InMemoryEventRepository,
)


@pytest.fixture
def run_repository():
    return InMemoryRunRepository()


@pytest.fixture
def event_repository():
    return InMemoryEventRepository()


@pytest.fixture
def use_case(run_repository, event_repository):
    return GetTimelineUseCase(
        run_repository=run_repository,
        event_repository=event_repository,
    )


@pytest.fixture
def run_with_events(run_repository, event_repository):
    """Create a run with some events."""
    run = Run.create(goal="테스트")
    run.start()
    run_repository.save(run)

    # Add events
    for i in range(5):
        event = Event.create(
            event_id=event_repository.next_id(),
            run_id=run.id,
            event_type=EventType.INFO,
            data={"message": f"이벤트 {i + 1}"},
        )
        event_repository.save(event)

    return run


class TestGetTimelineUseCase:
    """Test GetTimelineUseCase."""

    def test_get_timeline_success(
        self, use_case, run_with_events
    ):
        request = GetTimelineRequest(run_id=run_with_events.id)

        response = use_case.execute(request)

        assert response.run_id == run_with_events.id
        assert len(response.events) == 5
        assert response.has_more is False

    def test_get_timeline_with_limit(
        self, use_case, run_with_events
    ):
        request = GetTimelineRequest(run_id=run_with_events.id, limit=3)

        response = use_case.execute(request)

        assert len(response.events) == 3
        assert response.has_more is True

    def test_get_timeline_since_cursor(
        self, use_case, run_with_events, event_repository
    ):
        # Get first event ID
        events = event_repository.find_by_run(run_with_events.id, limit=1)
        first_event_id = events[0].id

        request = GetTimelineRequest(
            run_id=run_with_events.id,
            since_event_id=first_event_id,
        )

        response = use_case.execute(request)

        # Should return events after the first one
        assert len(response.events) == 4
        assert all(e.id > first_event_id for e in response.events)

    def test_get_timeline_empty(self, use_case, run_repository):
        # Create run without events
        run = Run.create(goal="빈 런")
        run.start()
        run_repository.save(run)

        request = GetTimelineRequest(run_id=run.id)

        response = use_case.execute(request)

        assert len(response.events) == 0
        assert response.latest_event_id is None
        assert response.has_more is False

    def test_get_timeline_run_not_found(self, use_case):
        request = GetTimelineRequest(run_id="nonexistent")

        with pytest.raises(NotFoundError) as exc_info:
            use_case.execute(request)

        assert exc_info.value.entity_type == "Run"

    def test_timeline_event_format(self, use_case, run_with_events):
        request = GetTimelineRequest(run_id=run_with_events.id, limit=1)

        response = use_case.execute(request)

        event = response.events[0]
        assert event.id is not None
        assert event.type == "info"
        assert event.timestamp is not None
        assert event.summary is not None
        assert isinstance(event.data, dict)

    def test_latest_event_id_is_set(self, use_case, run_with_events):
        request = GetTimelineRequest(run_id=run_with_events.id)

        response = use_case.execute(request)

        assert response.latest_event_id is not None
        assert response.latest_event_id == response.events[-1].id
