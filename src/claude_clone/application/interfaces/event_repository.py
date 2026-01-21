"""EventRepository interface - Abstract repository for Event entities."""

from abc import ABC, abstractmethod
from typing import Optional

from claude_clone.domain.entities.event import Event, EventType


class EventRepository(ABC):
    """Abstract repository for Event persistence.

    Events are immutable - only save and query, no update or delete.

    Implementations:
    - InMemoryEventRepository (testing)
    - SqliteEventRepository (production)
    """

    @abstractmethod
    def save(self, event: Event) -> None:
        """Save an event."""
        ...

    @abstractmethod
    def find_by_id(self, event_id: int) -> Optional[Event]:
        """Find an event by ID. Returns None if not found."""
        ...

    @abstractmethod
    def find_by_run(
        self,
        run_id: str,
        since_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[Event]:
        """Find events for a run, optionally since a given event ID."""
        ...

    @abstractmethod
    def find_by_type(
        self,
        run_id: str,
        event_type: EventType,
        limit: int = 100,
    ) -> list[Event]:
        """Find events of a specific type for a run."""
        ...

    @abstractmethod
    def get_latest_id(self, run_id: str) -> Optional[int]:
        """Get the latest event ID for a run."""
        ...

    @abstractmethod
    def count_by_run(self, run_id: str) -> int:
        """Count events for a run."""
        ...

    @abstractmethod
    def next_id(self) -> int:
        """Get the next available event ID."""
        ...
