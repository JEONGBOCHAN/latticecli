"""Dependency Injection Container.

Wires together all layers of the application.
"""

from typing import TypeVar, Type, Optional

from claude_clone.application.interfaces.run_repository import RunRepository
from claude_clone.application.interfaces.approval_repository import ApprovalRepository
from claude_clone.application.interfaces.event_repository import EventRepository
from claude_clone.application.interfaces.event_publisher import EventPublisher
from claude_clone.application.use_cases.create_run import CreateRunUseCase
from claude_clone.application.use_cases.resolve_approval import ResolveApprovalUseCase
from claude_clone.application.use_cases.get_timeline import GetTimelineUseCase
from claude_clone.adapters.persistence.in_memory import (
    InMemoryRunRepository,
    InMemoryApprovalRepository,
    InMemoryEventRepository,
)
from claude_clone.adapters.messaging.event_bus import EventBus

T = TypeVar("T")


class DIContainer:
    """Simple dependency injection container.

    Usage:
        container = DIContainer()
        container.configure_in_memory()  # For testing

        # Get dependencies
        run_repo = container.get(RunRepository)
        use_case = container.get(CreateRunUseCase)
    """

    def __init__(self) -> None:
        self._instances: dict[type, object] = {}
        self._factories: dict[type, callable] = {}

    def register_instance(self, interface: type, instance: object) -> None:
        """Register a singleton instance."""
        self._instances[interface] = instance

    def register_factory(self, interface: type, factory: callable) -> None:
        """Register a factory function."""
        self._factories[interface] = factory

    def get(self, interface: Type[T]) -> T:
        """Get an instance of the requested type."""
        # Check for singleton
        if interface in self._instances:
            return self._instances[interface]  # type: ignore

        # Check for factory
        if interface in self._factories:
            instance = self._factories[interface]()
            return instance  # type: ignore

        raise KeyError(f"No registration found for {interface}")

    def configure_in_memory(self) -> "DIContainer":
        """Configure container with in-memory implementations (for testing)."""
        # Repositories
        run_repo = InMemoryRunRepository()
        approval_repo = InMemoryApprovalRepository()
        event_repo = InMemoryEventRepository()

        self.register_instance(RunRepository, run_repo)
        self.register_instance(ApprovalRepository, approval_repo)
        self.register_instance(EventRepository, event_repo)

        # Event publisher (with repository for persistence)
        event_bus = EventBus(event_repository=event_repo)
        self.register_instance(EventPublisher, event_bus)

        # Use cases
        self.register_factory(
            CreateRunUseCase,
            lambda: CreateRunUseCase(
                run_repository=self.get(RunRepository),
                event_publisher=self.get(EventPublisher),
            ),
        )

        self.register_factory(
            ResolveApprovalUseCase,
            lambda: ResolveApprovalUseCase(
                approval_repository=self.get(ApprovalRepository),
                event_publisher=self.get(EventPublisher),
            ),
        )

        self.register_factory(
            GetTimelineUseCase,
            lambda: GetTimelineUseCase(
                run_repository=self.get(RunRepository),
                event_repository=self.get(EventRepository),
            ),
        )

        return self

    def configure_sqlite(self, db_path: str = "ops_board.db") -> "DIContainer":
        """Configure container with SQLite implementations (for production).

        TODO: Implement in Phase 7
        """
        raise NotImplementedError("SQLite configuration will be implemented in Phase 7")


# Global container instance (optional - can also create per-request)
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get or create the global container instance."""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def reset_container() -> None:
    """Reset the global container (for testing)."""
    global _container
    _container = None
