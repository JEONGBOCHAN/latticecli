"""Tests for EventBus."""

import pytest

from claude_clone.domain.entities.event import Event, EventType
from claude_clone.adapters.messaging.event_bus import EventBus
from claude_clone.adapters.persistence.in_memory import InMemoryEventRepository


class TestEventBusPublish:
    """Test EventBus publish functionality."""

    @pytest.fixture
    def event_repository(self):
        return InMemoryEventRepository()

    @pytest.fixture
    def event_bus(self, event_repository):
        return EventBus(event_repository=event_repository)

    def test_publish_creates_event(self, event_bus):
        event = event_bus.publish(
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
            data={"goal": "테스트"},
        )

        assert event is not None
        assert event.run_id == "run-123"
        assert event.type == EventType.RUN_STARTED
        assert event.data["goal"] == "테스트"

    def test_publish_persists_event(self, event_bus, event_repository):
        event = event_bus.publish(
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
            data={},
        )

        saved = event_repository.find_by_id(event.id)

        assert saved is not None
        assert saved.id == event.id

    def test_publish_without_repository(self):
        event_bus = EventBus(event_repository=None)

        event = event_bus.publish(
            run_id="run-123",
            event_type=EventType.INFO,
            data={},
        )

        assert event is not None
        assert event.id == 0  # No persistence

    def test_publish_assigns_sequential_ids(self, event_bus):
        event1 = event_bus.publish(
            run_id="run-123",
            event_type=EventType.INFO,
            data={},
        )
        event2 = event_bus.publish(
            run_id="run-123",
            event_type=EventType.INFO,
            data={},
        )
        event3 = event_bus.publish(
            run_id="run-123",
            event_type=EventType.INFO,
            data={},
        )

        assert event1.id == 1
        assert event2.id == 2
        assert event3.id == 3


class TestEventBusSubscribe:
    """Test EventBus subscription functionality."""

    @pytest.fixture
    def event_bus(self):
        return EventBus()

    def test_subscribe_receives_events(self, event_bus):
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe(EventType.RUN_STARTED, handler)
        event_bus.publish(
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
            data={},
        )

        assert len(received_events) == 1
        assert received_events[0].type == EventType.RUN_STARTED

    def test_subscribe_only_receives_matching_type(self, event_bus):
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe(EventType.RUN_STARTED, handler)
        event_bus.publish(
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
            data={},
        )
        event_bus.publish(
            run_id="run-123",
            event_type=EventType.TOOL_CALLED,
            data={},
        )

        assert len(received_events) == 1

    def test_subscribe_all_receives_all_events(self, event_bus):
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe_all(handler)
        event_bus.publish(
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
            data={},
        )
        event_bus.publish(
            run_id="run-123",
            event_type=EventType.TOOL_CALLED,
            data={},
        )

        assert len(received_events) == 2

    def test_multiple_subscribers(self, event_bus):
        received1 = []
        received2 = []

        def handler1(event):
            received1.append(event)

        def handler2(event):
            received2.append(event)

        event_bus.subscribe(EventType.RUN_STARTED, handler1)
        event_bus.subscribe(EventType.RUN_STARTED, handler2)
        event_bus.publish(
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
            data={},
        )

        assert len(received1) == 1
        assert len(received2) == 1

    def test_unsubscribe(self, event_bus):
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe(EventType.INFO, handler)
        event_bus.publish(run_id="run-123", event_type=EventType.INFO, data={})

        event_bus.unsubscribe(EventType.INFO, handler)
        event_bus.publish(run_id="run-123", event_type=EventType.INFO, data={})

        assert len(received_events) == 1  # Only first event

    def test_unsubscribe_all(self, event_bus):
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe_all(handler)
        event_bus.publish(run_id="run-123", event_type=EventType.INFO, data={})

        event_bus.unsubscribe_all(handler)
        event_bus.publish(run_id="run-123", event_type=EventType.INFO, data={})

        assert len(received_events) == 1

    def test_clear_handlers(self, event_bus):
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe(EventType.INFO, handler)
        event_bus.subscribe_all(handler)
        event_bus.clear_handlers()

        event_bus.publish(run_id="run-123", event_type=EventType.INFO, data={})

        assert len(received_events) == 0

    def test_duplicate_subscription_prevented(self, event_bus):
        received_events = []

        def handler(event):
            received_events.append(event)

        event_bus.subscribe(EventType.INFO, handler)
        event_bus.subscribe(EventType.INFO, handler)  # Duplicate

        event_bus.publish(run_id="run-123", event_type=EventType.INFO, data={})

        assert len(received_events) == 1  # Should only receive once
