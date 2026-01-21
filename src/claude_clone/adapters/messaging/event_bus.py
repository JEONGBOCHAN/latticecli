"""EventBus - In-process event publishing implementation."""

from collections import defaultdict
from typing import Any, Callable, Optional

from claude_clone.domain.entities.event import Event, EventType
from claude_clone.application.interfaces.event_publisher import EventPublisher
from claude_clone.application.interfaces.event_repository import EventRepository


class EventBus(EventPublisher):
    """In-process event bus for publishing and subscribing to events.

    Features:
    - Synchronous event delivery
    - Multiple subscribers per event type
    - Optional persistence via EventRepository
    """

    def __init__(self, event_repository: Optional[EventRepository] = None) -> None:
        self._event_repository = event_repository
        self._handlers: dict[EventType, list[Callable[[Event], None]]] = defaultdict(
            list
        )
        self._global_handlers: list[Callable[[Event], None]] = []

    def publish(
        self,
        run_id: str,
        event_type: EventType,
        data: Optional[dict[str, Any]] = None,
    ) -> Event:
        """Publish an event and return the created Event."""
        # Get next ID
        if self._event_repository:
            event_id = self._event_repository.next_id()
        else:
            event_id = 0  # No persistence

        # Create event
        event = Event.create(
            event_id=event_id,
            run_id=run_id,
            event_type=event_type,
            data=data,
        )

        # Persist if repository available
        if self._event_repository:
            self._event_repository.save(event)

        # Notify handlers
        self._notify(event)

        return event

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
    ) -> None:
        """Subscribe to events of a specific type."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def subscribe_all(
        self,
        handler: Callable[[Event], None],
    ) -> None:
        """Subscribe to all events."""
        if handler not in self._global_handlers:
            self._global_handlers.append(handler)

    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
    ) -> None:
        """Unsubscribe a handler from an event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def unsubscribe_all(
        self,
        handler: Callable[[Event], None],
    ) -> None:
        """Unsubscribe a global handler."""
        if handler in self._global_handlers:
            self._global_handlers.remove(handler)

    def _notify(self, event: Event) -> None:
        """Notify all relevant handlers."""
        # Type-specific handlers
        for handler in self._handlers[event.type]:
            handler(event)

        # Global handlers
        for handler in self._global_handlers:
            handler(event)

    def clear_handlers(self) -> None:
        """Clear all handlers (for testing)."""
        self._handlers.clear()
        self._global_handlers.clear()
