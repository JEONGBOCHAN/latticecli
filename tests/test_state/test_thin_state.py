"""Tests for ThinState."""

import pytest

from claude_clone.state.thin import ThinState
from claude_clone.state.types import RepoInfo


class TestThinStateCreation:
    """Test ThinState creation."""

    def test_create_default(self):
        state = ThinState()

        assert state.run_id.startswith("run-")
        assert state.turn == 0
        assert state.goal == ""

    def test_create_with_new_run(self):
        state = ThinState.new_run(goal="인증 구현", repo_root="/home/user/project")

        assert state.goal == "인증 구현"
        assert state.repo["root"] == "/home/user/project"

    def test_run_id_is_unique(self):
        state1 = ThinState()
        state2 = ThinState()

        assert state1.run_id != state2.run_id


class TestThinStateTurnManagement:
    """Test ThinState turn management."""

    def test_increment_turn(self):
        state = ThinState()

        assert state.turn == 0

        state.increment_turn()
        assert state.turn == 1

        state.increment_turn()
        assert state.turn == 2

    def test_set_goal(self):
        state = ThinState()

        state.set_goal("새로운 목표")

        assert state.goal == "새로운 목표"


class TestThinStateApprovals:
    """Test ThinState approval management."""

    def test_add_pending_approval(self):
        state = ThinState()

        state.add_pending_approval("apr-001")

        assert "apr-001" in state.approvals["pending_ids"]
        assert state.approvals["pending_count"] == 1
        assert state.approvals["focus_approval_id"] == "apr-001"

    def test_add_multiple_approvals(self):
        state = ThinState()

        state.add_pending_approval("apr-001")
        state.add_pending_approval("apr-002")
        state.add_pending_approval("apr-003")

        assert len(state.approvals["pending_ids"]) == 3
        assert state.approvals["pending_count"] == 3
        # Focus should remain on first one
        assert state.approvals["focus_approval_id"] == "apr-001"

    def test_add_duplicate_approval_ignored(self):
        state = ThinState()

        state.add_pending_approval("apr-001")
        state.add_pending_approval("apr-001")  # Duplicate

        assert state.approvals["pending_count"] == 1

    def test_remove_pending_approval(self):
        state = ThinState()
        state.add_pending_approval("apr-001")
        state.add_pending_approval("apr-002")

        state.remove_pending_approval("apr-001")

        assert "apr-001" not in state.approvals["pending_ids"]
        assert state.approvals["pending_count"] == 1
        # Focus should shift to next
        assert state.approvals["focus_approval_id"] == "apr-002"

    def test_remove_all_approvals_clears_focus(self):
        state = ThinState()
        state.add_pending_approval("apr-001")

        state.remove_pending_approval("apr-001")

        assert state.approvals["pending_count"] == 0
        assert state.approvals["focus_approval_id"] is None


class TestThinStateEvents:
    """Test ThinState event management."""

    def test_add_event_digest(self):
        state = ThinState()

        state.add_event_digest("파일 생성: main.py")

        assert len(state.recent_events_digest) == 1
        assert state.recent_events_digest[0] == "파일 생성: main.py"

    def test_event_digest_max_limit(self):
        state = ThinState()

        for i in range(15):
            state.add_event_digest(f"이벤트 {i}", max_events=10)

        assert len(state.recent_events_digest) == 10
        # Should keep most recent
        assert state.recent_events_digest[0] == "이벤트 5"
        assert state.recent_events_digest[-1] == "이벤트 14"

    def test_update_event_cursor(self):
        state = ThinState()

        state.update_event_cursor(event_id=42, ts="2024-01-15T10:30:00Z")

        assert state.event_cursor["last_event_id"] == 42
        assert state.event_cursor["last_ts"] == "2024-01-15T10:30:00Z"


class TestThinStateSerialization:
    """Test ThinState serialization."""

    def test_to_dict(self):
        state = ThinState.new_run(goal="테스트", repo_root="/project")
        state.increment_turn()
        state.add_pending_approval("apr-001")

        result = state.to_dict()

        assert result["goal"] == "테스트"
        assert result["turn"] == 1
        assert result["repo"]["root"] == "/project"
        assert result["approvals"]["pending_count"] == 1

    def test_to_context_string_basic(self):
        state = ThinState.new_run(goal="인증 시스템 구현")
        state.increment_turn()

        context = state.to_context_string()

        assert state.run_id in context
        assert "Turn: 1" in context
        assert "인증 시스템 구현" in context

    def test_to_context_string_with_approvals(self):
        state = ThinState()
        state.add_pending_approval("apr-001")
        state.add_pending_approval("apr-002")

        context = state.to_context_string()

        assert "Pending approvals: 2" in context
        assert "apr-001" in context

    def test_to_context_string_with_events(self):
        state = ThinState()
        state.add_event_digest("파일 읽기: main.py")
        state.add_event_digest("파일 수정: config.py")

        context = state.to_context_string()

        assert "Recent events:" in context
        assert "main.py" in context
        assert "config.py" in context

    def test_to_context_string_no_goal(self):
        state = ThinState()

        context = state.to_context_string()

        assert "Goal: (not set)" in context
