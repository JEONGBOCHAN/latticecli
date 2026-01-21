"""Tests for DIContainer."""

import pytest

from claude_clone.infrastructure.container import (
    DIContainer,
    get_container,
    reset_container,
)
from claude_clone.application.interfaces.run_repository import RunRepository
from claude_clone.application.interfaces.approval_repository import ApprovalRepository
from claude_clone.application.interfaces.event_repository import EventRepository
from claude_clone.application.interfaces.event_publisher import EventPublisher
from claude_clone.application.use_cases.create_run import CreateRunUseCase
from claude_clone.application.use_cases.resolve_approval import ResolveApprovalUseCase
from claude_clone.application.use_cases.get_timeline import GetTimelineUseCase


class TestDIContainerBasic:
    """Test DIContainer basic functionality."""

    def test_register_and_get_instance(self):
        container = DIContainer()
        instance = object()

        container.register_instance(object, instance)
        retrieved = container.get(object)

        assert retrieved is instance

    def test_register_and_get_factory(self):
        container = DIContainer()
        created_instances = []

        def factory():
            obj = object()
            created_instances.append(obj)
            return obj

        container.register_factory(object, factory)
        instance1 = container.get(object)
        instance2 = container.get(object)

        # Factory creates new instance each time
        assert len(created_instances) == 2
        assert instance1 is not instance2

    def test_get_not_registered_raises(self):
        container = DIContainer()

        with pytest.raises(KeyError) as exc_info:
            container.get(str)

        assert "str" in str(exc_info.value)


class TestDIContainerInMemoryConfiguration:
    """Test DIContainer in-memory configuration."""

    @pytest.fixture
    def container(self):
        return DIContainer().configure_in_memory()

    def test_repositories_are_registered(self, container):
        run_repo = container.get(RunRepository)
        approval_repo = container.get(ApprovalRepository)
        event_repo = container.get(EventRepository)

        assert run_repo is not None
        assert approval_repo is not None
        assert event_repo is not None

    def test_event_publisher_is_registered(self, container):
        publisher = container.get(EventPublisher)

        assert publisher is not None

    def test_use_cases_are_registered(self, container):
        create_run = container.get(CreateRunUseCase)
        resolve_approval = container.get(ResolveApprovalUseCase)
        get_timeline = container.get(GetTimelineUseCase)

        assert create_run is not None
        assert resolve_approval is not None
        assert get_timeline is not None

    def test_repositories_are_singletons(self, container):
        repo1 = container.get(RunRepository)
        repo2 = container.get(RunRepository)

        assert repo1 is repo2

    def test_use_cases_share_same_repositories(self, container):
        from claude_clone.domain.entities.run import Run

        # Create a run via use case
        create_run = container.get(CreateRunUseCase)
        from claude_clone.application.use_cases.create_run import CreateRunRequest

        response = create_run.execute(CreateRunRequest(goal="테스트"))

        # Should be findable via repository
        repo = container.get(RunRepository)
        run = repo.find_by_id(response.run_id)

        assert run is not None
        assert run.goal == "테스트"


class TestDIContainerGlobal:
    """Test global container functions."""

    def teardown_method(self):
        reset_container()

    def test_get_container_creates_once(self):
        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_reset_container(self):
        container1 = get_container()
        reset_container()
        container2 = get_container()

        assert container1 is not container2


class TestDIContainerSQLiteConfiguration:
    """Test DIContainer SQLite configuration."""

    def test_sqlite_not_implemented(self):
        container = DIContainer()

        with pytest.raises(NotImplementedError) as exc_info:
            container.configure_sqlite()

        assert "Phase 7" in str(exc_info.value)
