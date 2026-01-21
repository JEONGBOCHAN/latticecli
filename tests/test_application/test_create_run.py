"""Tests for CreateRunUseCase."""

import pytest

from claude_clone.domain.entities.run import RunStatus
from claude_clone.domain.entities.event import EventType
from claude_clone.application.use_cases.create_run import (
    CreateRunUseCase,
    CreateRunRequest,
)
from claude_clone.adapters.persistence.in_memory import (
    InMemoryRunRepository,
    InMemoryEventRepository,
)
from claude_clone.adapters.messaging.event_bus import EventBus


@pytest.fixture
def run_repository():
    return InMemoryRunRepository()


@pytest.fixture
def event_repository():
    return InMemoryEventRepository()


@pytest.fixture
def event_publisher(event_repository):
    return EventBus(event_repository=event_repository)


@pytest.fixture
def use_case(run_repository, event_publisher):
    return CreateRunUseCase(
        run_repository=run_repository,
        event_publisher=event_publisher,
    )


class TestCreateRunUseCase:
    """Test CreateRunUseCase."""

    def test_create_run_success(self, use_case, run_repository):
        request = CreateRunRequest(goal="인증 시스템 구현")

        response = use_case.execute(request)

        assert response.run_id.startswith("run-")
        assert response.status == "running"

        # Verify saved to repository
        run = run_repository.find_by_id(response.run_id)
        assert run is not None
        assert run.goal == "인증 시스템 구현"
        assert run.status == RunStatus.RUNNING

    def test_create_run_with_repo_root(self, use_case, run_repository):
        request = CreateRunRequest(
            goal="테스트", repo_root="/home/user/project"
        )

        response = use_case.execute(request)

        run = run_repository.find_by_id(response.run_id)
        assert run.repo_root == "/home/user/project"

    def test_create_run_with_branch(self, use_case, run_repository):
        request = CreateRunRequest(
            goal="테스트", repo_root=".", branch="feature/auth"
        )

        response = use_case.execute(request)

        run = run_repository.find_by_id(response.run_id)
        assert run.branch == "feature/auth"

    def test_create_run_emits_event(
        self, use_case, event_repository
    ):
        request = CreateRunRequest(goal="테스트 작업")

        response = use_case.execute(request)

        # Verify event was emitted
        events = event_repository.find_by_run(response.run_id)
        assert len(events) == 1
        assert events[0].type == EventType.RUN_STARTED
        assert events[0].data["goal"] == "테스트 작업"

    def test_create_multiple_runs(self, use_case, run_repository):
        request1 = CreateRunRequest(goal="작업 1")
        request2 = CreateRunRequest(goal="작업 2")

        response1 = use_case.execute(request1)
        response2 = use_case.execute(request2)

        assert response1.run_id != response2.run_id
        assert run_repository.count() == 2
