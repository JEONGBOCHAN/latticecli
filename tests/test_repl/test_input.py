"""Tests for REPL Input"""

from unittest.mock import MagicMock, patch

import pytest

from claude_clone.repl.input import (
    create_key_bindings,
    reset_session,
)


@pytest.fixture(autouse=True)
def reset_session_fixture() -> None:
    """Reset session before each test"""
    reset_session()
    yield
    reset_session()


class TestCreateKeyBindings:
    """Tests for create_key_bindings function"""

    def test_returns_key_bindings(self) -> None:
        """Test that key bindings are created"""
        from prompt_toolkit.key_binding import KeyBindings

        bindings = create_key_bindings()

        assert isinstance(bindings, KeyBindings)


class TestCreatePromptSession:
    """Tests for create_prompt_session function"""

    @patch("claude_clone.repl.input.PromptSession")
    def test_returns_session(self, mock_session_class: MagicMock) -> None:
        """Test that session is created"""
        from claude_clone.repl.input import create_prompt_session

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        session = create_prompt_session()

        assert session is mock_session
        mock_session_class.assert_called_once()

    @patch("claude_clone.repl.input.PromptSession")
    def test_session_has_history(self, mock_session_class: MagicMock) -> None:
        """Test that session is created with history"""
        from claude_clone.repl.input import create_prompt_session

        create_prompt_session()

        # Check that InMemoryHistory was passed
        call_kwargs = mock_session_class.call_args.kwargs
        assert "history" in call_kwargs
        assert call_kwargs["history"] is not None

    @patch("claude_clone.repl.input.PromptSession")
    def test_session_has_key_bindings(self, mock_session_class: MagicMock) -> None:
        """Test that session is created with key bindings"""
        from claude_clone.repl.input import create_prompt_session

        create_prompt_session()

        # Check that key_bindings was passed
        call_kwargs = mock_session_class.call_args.kwargs
        assert "key_bindings" in call_kwargs
        assert call_kwargs["key_bindings"] is not None


class TestGetPromptSession:
    """Tests for get_prompt_session function"""

    @patch("claude_clone.repl.input.create_prompt_session")
    def test_returns_session(self, mock_create: MagicMock) -> None:
        """Test that session is returned"""
        from claude_clone.repl.input import get_prompt_session

        mock_session = MagicMock()
        mock_create.return_value = mock_session

        session = get_prompt_session()

        assert session is mock_session

    @patch("claude_clone.repl.input.create_prompt_session")
    def test_returns_same_instance(self, mock_create: MagicMock) -> None:
        """Test that same session instance is returned"""
        from claude_clone.repl.input import get_prompt_session

        mock_session = MagicMock()
        mock_create.return_value = mock_session

        session1 = get_prompt_session()
        session2 = get_prompt_session()

        assert session1 is session2
        # Should only create once
        mock_create.assert_called_once()

    @patch("claude_clone.repl.input.create_prompt_session")
    def test_reset_creates_new_instance(self, mock_create: MagicMock) -> None:
        """Test that reset creates new instance"""
        from claude_clone.repl.input import get_prompt_session

        mock_session1 = MagicMock()
        mock_session2 = MagicMock()
        mock_create.side_effect = [mock_session1, mock_session2]

        session1 = get_prompt_session()
        reset_session()
        session2 = get_prompt_session()

        assert session1 is not session2
        assert mock_create.call_count == 2


class TestGetUserInput:
    """Tests for get_user_input function"""

    @patch("claude_clone.repl.input.get_prompt_session")
    def test_returns_stripped_input(self, mock_get_session: MagicMock) -> None:
        """Test that input is stripped"""
        from claude_clone.repl.input import get_user_input

        mock_session = MagicMock()
        mock_session.prompt.return_value = "  hello world  "
        mock_get_session.return_value = mock_session

        result = get_user_input()

        assert result == "hello world"

    @patch("claude_clone.repl.input.get_prompt_session")
    def test_uses_custom_prompt(self, mock_get_session: MagicMock) -> None:
        """Test that custom prompt is used"""
        from claude_clone.repl.input import get_user_input

        mock_session = MagicMock()
        mock_session.prompt.return_value = "test"
        mock_get_session.return_value = mock_session

        get_user_input(prompt=">>> ")

        mock_session.prompt.assert_called_once_with(">>> ")

    @patch("claude_clone.repl.input.get_prompt_session")
    def test_default_prompt(self, mock_get_session: MagicMock) -> None:
        """Test that default prompt is used"""
        from claude_clone.repl.input import get_user_input

        mock_session = MagicMock()
        mock_session.prompt.return_value = "test"
        mock_get_session.return_value = mock_session

        get_user_input()

        mock_session.prompt.assert_called_once_with("> ")
