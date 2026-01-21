"""Tests for Task entity."""

import pytest

from claude_clone.domain.entities.task import Task, TaskStatus
from claude_clone.domain.exceptions import InvalidStateError


class TestTaskCreation:
    """Test Task creation."""

    def test_create_task(self):
        task = Task.create(
            run_id="run-123",
            title="파일 검색",
            description="auth 관련 파일 찾기",
        )

        assert task.run_id == "run-123"
        assert task.title == "파일 검색"
        assert task.description == "auth 관련 파일 찾기"
        assert task.status == TaskStatus.PENDING
        assert task.id.startswith("task-")

    def test_create_task_with_priority(self):
        task = Task.create(
            run_id="run-123",
            title="긴급 작업",
            priority=10,
        )

        assert task.priority == 10

    def test_task_id_is_unique(self):
        task1 = Task.create(run_id="run-1", title="Task 1")
        task2 = Task.create(run_id="run-1", title="Task 2")

        assert task1.id != task2.id


class TestTaskStateTransitions:
    """Test Task state transitions."""

    def test_assign_task(self):
        task = Task.create(run_id="run-123", title="테스트")

        task.assign(worker_id="worker-1")

        assert task.status == TaskStatus.IN_PROGRESS
        assert task.owner_worker_id == "worker-1"

    def test_complete_task(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")

        task.complete()

        assert task.status == TaskStatus.COMPLETED

    def test_complete_task_with_outputs(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")

        task.complete(output_refs=["artifact-1", "artifact-2"])

        assert task.status == TaskStatus.COMPLETED
        assert "artifact-1" in task.output_refs
        assert "artifact-2" in task.output_refs

    def test_fail_task(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")

        task.fail(error_message="파일을 찾을 수 없음")

        assert task.status == TaskStatus.FAILED
        assert task.error_message == "파일을 찾을 수 없음"

    def test_block_task(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")

        task.block(reason="승인 대기 중")

        assert task.status == TaskStatus.BLOCKED
        assert task.error_message == "승인 대기 중"

    def test_unblock_task(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")
        task.block(reason="승인 대기 중")

        task.unblock()

        assert task.status == TaskStatus.IN_PROGRESS
        assert task.error_message is None


class TestTaskInvalidTransitions:
    """Test invalid state transitions."""

    def test_cannot_assign_already_assigned(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")

        with pytest.raises(InvalidStateError):
            task.assign(worker_id="worker-2")

    def test_cannot_complete_pending_task(self):
        task = Task.create(run_id="run-123", title="테스트")

        with pytest.raises(InvalidStateError):
            task.complete()

    def test_cannot_fail_pending_task(self):
        task = Task.create(run_id="run-123", title="테스트")

        with pytest.raises(InvalidStateError):
            task.fail(error_message="에러")

    def test_cannot_block_pending_task(self):
        task = Task.create(run_id="run-123", title="테스트")

        with pytest.raises(InvalidStateError):
            task.block()

    def test_cannot_unblock_running_task(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")

        with pytest.raises(InvalidStateError):
            task.unblock()


class TestTaskProperties:
    """Test Task properties."""

    def test_is_active_when_pending(self):
        task = Task.create(run_id="run-123", title="테스트")

        assert task.is_active is True
        assert task.is_terminal is False

    def test_is_active_when_in_progress(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")

        assert task.is_active is True
        assert task.is_terminal is False

    def test_is_active_when_blocked(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")
        task.block()

        assert task.is_active is True
        assert task.is_terminal is False

    def test_is_terminal_when_completed(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")
        task.complete()

        assert task.is_active is False
        assert task.is_terminal is True

    def test_is_terminal_when_failed(self):
        task = Task.create(run_id="run-123", title="테스트")
        task.assign(worker_id="worker-1")
        task.fail(error_message="에러")

        assert task.is_active is False
        assert task.is_terminal is True
