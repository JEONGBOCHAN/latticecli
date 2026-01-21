"""In-memory implementation of EventRepository for testing."""

from typing import Optional

from claude_clone.domain.entities.event import Event, EventType
from claude_clone.application.interfaces.event_repository import EventRepository


class InMemoryEventRepository(EventRepository):
    """In-memory implementation of EventRepository.

    Useful for:
    - Unit testing
    - Quick prototyping
    - Development without database
    """

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._next_id: int = 1

    def save(self, event: Event) -> None:
        """Save an event."""
        self._events.append(event)

    def find_by_id(self, event_id: int) -> Optional[Event]:
        """Find an event by ID. Returns None if not found."""
        for event in self._events:
            if event.id == event_id:
                return event
        return None

    def find_by_run(
        self,
        run_id: str,
        since_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[Event]:
        """Find events for a run, optionally since a given event ID."""
        events = [e for e in self._events if e.run_id == run_id]

        if since_id is not None:
            events = [e for e in events if e.id > since_id]

        # Sort by ID (ascending)
        events.sort(key=lambda e: e.id)

        return events[:limit]

    def find_by_type(
        self,
        run_id: str,
        event_type: EventType,
        limit: int = 100,
    ) -> list[Event]:
        """Find events of a specific type for a run."""
        events = [
            e
            for e in self._events
            if e.run_id == run_id and e.type == event_type
        ]
        events.sort(key=lambda e: e.id)
        return events[:limit]

    def get_latest_id(self, run_id: str) -> Optional[int]:
        """Get the latest event ID for a run."""
        events = [e for e in self._events if e.run_id == run_id]
        if not events:
            return None
        return max(e.id for e in events)

    def count_by_run(self, run_id: str) -> int:
        """Count events for a run."""
        return len([e for e in self._events if e.run_id == run_id])

    def next_id(self) -> int:
        """Get the next available event ID."""
        event_id = self._next_id
        self._next_id += 1
        return event_id

    def clear(self) -> None:
        """Clear all events (for testing)."""
        self._events.clear()
        self._next_id = 1

    def count(self) -> int:
        """Count total events (for testing)."""
        return len(self._events)
