"""Tests for Run entity."""

import pytest

from claude_clone.domain.entities.run import Run, RunStatus
from claude_clone.domain.exceptions import InvalidStateError


class TestRunCreation:
    """Test Run creation."""

    def test_create_run_with_goal(self):
        run = Run.create(goal="인증 시스템 구현")

        assert run.goal == "인증 시스템 구현"
        assert run.status == RunStatus.PENDING
        assert run.id.startswith("run-")
        assert run.repo_root == "."

    def test_create_run_with_repo_root(self):
        run = Run.create(goal="테스트", repo_root="/home/user/project")

        assert run.repo_root == "/home/user/project"

    def test_run_id_is_unique(self):
        run1 = Run.create(goal="테스트1")
        run2 = Run.create(goal="테스트2")

        assert run1.id != run2.id


class TestRunStateTransitions:
    """Test Run state transitions."""

    def test_pending_to_running(self):
        run = Run.create(goal="테스트")
        assert run.status == RunStatus.PENDING

        run.start()

        assert run.status == RunStatus.RUNNING

    def test_running_to_completed(self):
        run = Run.create(goal="테스트")
        run.start()

        run.complete()

        assert run.status == RunStatus.COMPLETED

    def test_running_to_failed(self):
        run = Run.create(goal="테스트")
        run.start()

        run.fail()

        assert run.status == RunStatus.FAILED

    def test_pending_to_cancelled(self):
        run = Run.create(goal="테스트")

        run.cancel()

        assert run.status == RunStatus.CANCELLED

    def test_running_to_cancelled(self):
        run = Run.create(goal="테스트")
        run.start()

        run.cancel()

        assert run.status == RunStatus.CANCELLED


class TestRunInvalidTransitions:
    """Test invalid state transitions raise errors."""

    def test_cannot_complete_pending_run(self):
        run = Run.create(goal="테스트")

        with pytest.raises(InvalidStateError):
            run.complete()

    def test_cannot_fail_pending_run(self):
        run = Run.create(goal="테스트")

        with pytest.raises(InvalidStateError):
            run.fail()

    def test_cannot_start_completed_run(self):
        run = Run.create(goal="테스트")
        run.start()
        run.complete()

        with pytest.raises(InvalidStateError):
            run.start()

    def test_cannot_complete_twice(self):
        run = Run.create(goal="테스트")
        run.start()
        run.complete()

        with pytest.raises(InvalidStateError):
            run.complete()

    def test_cannot_cancel_completed_run(self):
        run = Run.create(goal="테스트")
        run.start()
        run.complete()

        with pytest.raises(InvalidStateError):
            run.cancel()


class TestRunProperties:
    """Test Run properties."""

    def test_is_active_when_pending(self):
        run = Run.create(goal="테스트")

        assert run.is_active is True
        assert run.is_terminal is False

    def test_is_active_when_running(self):
        run = Run.create(goal="테스트")
        run.start()

        assert run.is_active is True
        assert run.is_terminal is False

    def test_is_terminal_when_completed(self):
        run = Run.create(goal="테스트")
        run.start()
        run.complete()

        assert run.is_active is False
        assert run.is_terminal is True

    def test_is_terminal_when_failed(self):
        run = Run.create(goal="테스트")
        run.start()
        run.fail()

        assert run.is_active is False
        assert run.is_terminal is True

    def test_is_terminal_when_cancelled(self):
        run = Run.create(goal="테스트")
        run.cancel()

        assert run.is_active is False
        assert run.is_terminal is True
