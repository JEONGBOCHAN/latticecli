"""EventPublisher interface - Abstract interface for publishing events."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from claude_clone.domain.entities.event import Event, EventType


class EventPublisher(ABC):
    """Abstract interface for publishing and subscribing to events.

    This is an in-process event bus, not a message queue.

    Implementations:
    - InMemoryEventPublisher (testing)
    - EventBus (production)
    """

    @abstractmethod
    def publish(
        self,
        run_id: str,
        event_type: EventType,
        data: Optional[dict[str, Any]] = None,
    ) -> Event:
        """Publish an event and return the created Event."""
        ...

    @abstractmethod
    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
    ) -> None:
        """Subscribe to events of a specific type."""
        ...

    @abstractmethod
    def subscribe_all(
        self,
        handler: Callable[[Event], None],
    ) -> None:
        """Subscribe to all events."""
        ...

    @abstractmethod
    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
    ) -> None:
        """Unsubscribe a handler from an event type."""
        ...
