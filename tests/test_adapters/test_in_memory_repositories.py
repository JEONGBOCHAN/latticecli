"""Tests for in-memory repository implementations."""

import pytest

from claude_clone.domain.entities.run import Run, RunStatus
from claude_clone.domain.entities.approval import Approval, ApprovalType, ApprovalStatus
from claude_clone.domain.entities.event import Event, EventType
from claude_clone.adapters.persistence.in_memory import (
    InMemoryRunRepository,
    InMemoryApprovalRepository,
    InMemoryEventRepository,
)


class TestInMemoryRunRepository:
    """Test InMemoryRunRepository."""

    @pytest.fixture
    def repo(self):
        return InMemoryRunRepository()

    def test_save_and_find_by_id(self, repo):
        run = Run.create(goal="테스트")
        repo.save(run)

        found = repo.find_by_id(run.id)

        assert found is not None
        assert found.id == run.id
        assert found.goal == "테스트"

    def test_find_by_id_not_found(self, repo):
        found = repo.find_by_id("nonexistent")

        assert found is None

    def test_find_active(self, repo):
        # Create runs with different statuses
        active_run = Run.create(goal="활성")
        active_run.start()
        repo.save(active_run)

        completed_run = Run.create(goal="완료")
        completed_run.start()
        completed_run.complete()
        repo.save(completed_run)

        active_runs = repo.find_active()

        assert len(active_runs) == 1
        assert active_runs[0].id == active_run.id

    def test_find_by_status(self, repo):
        run1 = Run.create(goal="실행 중 1")
        run1.start()
        repo.save(run1)

        run2 = Run.create(goal="실행 중 2")
        run2.start()
        repo.save(run2)

        run3 = Run.create(goal="대기 중")
        repo.save(run3)

        running = repo.find_by_status(RunStatus.RUNNING)

        assert len(running) == 2

    def test_list_recent(self, repo):
        for i in range(5):
            run = Run.create(goal=f"런 {i}")
            repo.save(run)

        recent = repo.list_recent(limit=3)

        assert len(recent) == 3

    def test_delete(self, repo):
        run = Run.create(goal="삭제 예정")
        repo.save(run)

        deleted = repo.delete(run.id)

        assert deleted is True
        assert repo.find_by_id(run.id) is None

    def test_delete_not_found(self, repo):
        deleted = repo.delete("nonexistent")

        assert deleted is False

    def test_clear_and_count(self, repo):
        repo.save(Run.create(goal="런 1"))
        repo.save(Run.create(goal="런 2"))

        assert repo.count() == 2

        repo.clear()

        assert repo.count() == 0


class TestInMemoryApprovalRepository:
    """Test InMemoryApprovalRepository."""

    @pytest.fixture
    def repo(self):
        return InMemoryApprovalRepository()

    def test_save_and_find_by_id(self, repo):
        approval = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="src/main.py",
        )
        repo.save(approval)

        found = repo.find_by_id(approval.id)

        assert found is not None
        assert found.id == approval.id

    def test_find_by_run(self, repo):
        approval1 = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="file1.py",
        )
        approval2 = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="file2.py",
        )
        approval3 = Approval.create(
            run_id="run-456",
            approval_type=ApprovalType.FILE_EDIT,
            target="file3.py",
        )
        repo.save(approval1)
        repo.save(approval2)
        repo.save(approval3)

        approvals = repo.find_by_run("run-123")

        assert len(approvals) == 2

    def test_find_pending_by_run(self, repo):
        pending = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="file1.py",
        )
        repo.save(pending)

        approved = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="file2.py",
        )
        approved.approve()
        repo.save(approved)

        pending_list = repo.find_pending_by_run("run-123")

        assert len(pending_list) == 1
        assert pending_list[0].id == pending.id

    def test_find_by_status(self, repo):
        pending = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="file1.py",
        )
        repo.save(pending)

        approved = Approval.create(
            run_id="run-123",
            approval_type=ApprovalType.FILE_EDIT,
            target="file2.py",
        )
        approved.approve()
        repo.save(approved)

        approved_list = repo.find_by_status("run-123", ApprovalStatus.APPROVED)

        assert len(approved_list) == 1
        assert approved_list[0].id == approved.id

    def test_count_pending(self, repo):
        for i in range(3):
            approval = Approval.create(
                run_id="run-123",
                approval_type=ApprovalType.FILE_EDIT,
                target=f"file{i}.py",
            )
            repo.save(approval)

        count = repo.count_pending("run-123")

        assert count == 3


class TestInMemoryEventRepository:
    """Test InMemoryEventRepository."""

    @pytest.fixture
    def repo(self):
        return InMemoryEventRepository()

    def test_save_and_find_by_id(self, repo):
        event = Event.create(
            event_id=repo.next_id(),
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
            data={"goal": "테스트"},
        )
        repo.save(event)

        found = repo.find_by_id(event.id)

        assert found is not None
        assert found.id == event.id

    def test_next_id_increments(self, repo):
        id1 = repo.next_id()
        id2 = repo.next_id()
        id3 = repo.next_id()

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_find_by_run(self, repo):
        for i in range(5):
            event = Event.create(
                event_id=repo.next_id(),
                run_id="run-123",
                event_type=EventType.INFO,
                data={"index": i},
            )
            repo.save(event)

        # Add event for different run
        other_event = Event.create(
            event_id=repo.next_id(),
            run_id="run-456",
            event_type=EventType.INFO,
            data={},
        )
        repo.save(other_event)

        events = repo.find_by_run("run-123")

        assert len(events) == 5
        assert all(e.run_id == "run-123" for e in events)

    def test_find_by_run_with_since_id(self, repo):
        for i in range(5):
            event = Event.create(
                event_id=repo.next_id(),
                run_id="run-123",
                event_type=EventType.INFO,
                data={"index": i},
            )
            repo.save(event)

        events = repo.find_by_run("run-123", since_id=2)

        assert len(events) == 3
        assert all(e.id > 2 for e in events)

    def test_find_by_run_with_limit(self, repo):
        for i in range(10):
            event = Event.create(
                event_id=repo.next_id(),
                run_id="run-123",
                event_type=EventType.INFO,
                data={},
            )
            repo.save(event)

        events = repo.find_by_run("run-123", limit=3)

        assert len(events) == 3

    def test_find_by_type(self, repo):
        event1 = Event.run_started(
            event_id=repo.next_id(),
            run_id="run-123",
            goal="테스트",
        )
        repo.save(event1)

        event2 = Event.tool_called(
            event_id=repo.next_id(),
            run_id="run-123",
            tool="read",
            args={},
        )
        repo.save(event2)

        event3 = Event.tool_called(
            event_id=repo.next_id(),
            run_id="run-123",
            tool="write",
            args={},
        )
        repo.save(event3)

        tool_events = repo.find_by_type("run-123", EventType.TOOL_CALLED)

        assert len(tool_events) == 2

    def test_get_latest_id(self, repo):
        for i in range(5):
            event = Event.create(
                event_id=repo.next_id(),
                run_id="run-123",
                event_type=EventType.INFO,
                data={},
            )
            repo.save(event)

        latest_id = repo.get_latest_id("run-123")

        assert latest_id == 5

    def test_get_latest_id_empty(self, repo):
        latest_id = repo.get_latest_id("run-123")

        assert latest_id is None

    def test_count_by_run(self, repo):
        for i in range(7):
            event = Event.create(
                event_id=repo.next_id(),
                run_id="run-123",
                event_type=EventType.INFO,
                data={},
            )
            repo.save(event)

        count = repo.count_by_run("run-123")

        assert count == 7

    def test_clear_resets_id(self, repo):
        for i in range(3):
            event = Event.create(
                event_id=repo.next_id(),
                run_id="run-123",
                event_type=EventType.INFO,
                data={},
            )
            repo.save(event)

        repo.clear()

        assert repo.count() == 0
        assert repo.next_id() == 1  # ID should reset
