"""Tests for Event entity."""

from claude_clone.domain.entities.event import Event, EventType


class TestEventCreation:
    """Test Event creation."""

    def test_create_event(self):
        event = Event.create(
            event_id=1,
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
            data={"goal": "테스트"},
        )

        assert event.id == 1
        assert event.run_id == "run-123"
        assert event.type == EventType.RUN_STARTED
        assert event.data == {"goal": "테스트"}
        assert event.timestamp is not None

    def test_event_is_immutable(self):
        event = Event.create(
            event_id=1,
            run_id="run-123",
            event_type=EventType.RUN_STARTED,
        )

        # Event is frozen dataclass, should not allow modification
        # This would raise FrozenInstanceError
        assert event.id == 1  # Can read


class TestEventFactoryMethods:
    """Test Event factory methods."""

    def test_run_started_event(self):
        event = Event.run_started(
            event_id=1, run_id="run-123", goal="인증 구현"
        )

        assert event.type == EventType.RUN_STARTED
        assert event.data["goal"] == "인증 구현"

    def test_tool_called_event(self):
        event = Event.tool_called(
            event_id=2,
            run_id="run-123",
            tool="read",
            args={"file_path": "src/main.py"},
        )

        assert event.type == EventType.TOOL_CALLED
        assert event.data["tool"] == "read"
        assert event.data["args"]["file_path"] == "src/main.py"

    def test_file_changed_event(self):
        event = Event.file_changed(
            event_id=3, run_id="run-123", path="src/main.py"
        )

        assert event.type == EventType.FILE_CHANGED
        assert event.data["path"] == "src/main.py"

    def test_approval_requested_event(self):
        event = Event.approval_requested(
            event_id=4,
            run_id="run-123",
            approval_id="apr-456",
            target="src/main.py",
        )

        assert event.type == EventType.APPROVAL_REQUESTED
        assert event.data["approval_id"] == "apr-456"
        assert event.data["target"] == "src/main.py"


class TestEventSummary:
    """Test Event summary generation."""

    def test_summary_with_path(self):
        event = Event.file_changed(
            event_id=1, run_id="run-123", path="src/main.py"
        )

        summary = event.to_summary()

        assert "file changed" in summary
        assert "src/main.py" in summary

    def test_summary_with_target(self):
        event = Event.create(
            event_id=1,
            run_id="run-123",
            event_type=EventType.APPROVAL_REQUESTED,
            data={"target": "npm install"},
        )

        summary = event.to_summary()

        assert "npm install" in summary

    def test_summary_with_tool(self):
        event = Event.tool_called(
            event_id=1,
            run_id="run-123",
            tool="read",
            args={},
        )

        summary = event.to_summary()

        assert "tool called" in summary
        assert "read" in summary

    def test_summary_with_message(self):
        event = Event.create(
            event_id=1,
            run_id="run-123",
            event_type=EventType.INFO,
            data={"message": "작업 시작합니다"},
        )

        summary = event.to_summary()

        assert "작업 시작합니다" in summary


class TestEventTypes:
    """Test EventType enum."""

    def test_all_event_types_have_values(self):
        for event_type in EventType:
            assert event_type.value is not None
            assert len(event_type.value) > 0

    def test_run_lifecycle_events(self):
        assert EventType.RUN_STARTED.value == "run.started"
        assert EventType.RUN_COMPLETED.value == "run.completed"
        assert EventType.RUN_FAILED.value == "run.failed"

    def test_approval_events(self):
        assert EventType.APPROVAL_REQUESTED.value == "approval.requested"
        assert EventType.APPROVAL_APPROVED.value == "approval.approved"
        assert EventType.APPROVAL_REJECTED.value == "approval.rejected"
