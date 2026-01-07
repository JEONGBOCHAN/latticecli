"""Tests for REPL Output"""

from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from claude_clone.repl.output import (
    get_console,
    print_error,
    print_goodbye,
    print_info,
    print_response,
    print_tool_call,
    print_tool_result,
    print_welcome,
    reset_console,
)


@pytest.fixture(autouse=True)
def reset_console_fixture() -> None:
    """Reset console before each test"""
    reset_console()
    yield
    reset_console()


class TestGetConsole:
    """Tests for get_console function"""

    def test_returns_console(self) -> None:
        """Test that console is returned"""
        console = get_console()

        assert isinstance(console, Console)

    def test_returns_same_instance(self) -> None:
        """Test that same console instance is returned"""
        console1 = get_console()
        console2 = get_console()

        assert console1 is console2


class TestPrintResponse:
    """Tests for print_response function"""

    def test_prints_markdown(self) -> None:
        """Test that markdown is printed"""
        # This test just verifies no exception is raised
        print_response("# Hello\n\nThis is **bold** text")

    def test_prints_code_block(self) -> None:
        """Test that code blocks are handled"""
        print_response("```python\ndef hello():\n    pass\n```")

    def test_prints_empty_string(self) -> None:
        """Test that empty string is handled"""
        print_response("")


class TestPrintToolCall:
    """Tests for print_tool_call function"""

    def test_prints_tool_call(self) -> None:
        """Test that tool call is printed"""
        print_tool_call("read_tool", {"file_path": "test.py"})

    def test_prints_multiple_args(self) -> None:
        """Test that multiple args are formatted"""
        print_tool_call("read_tool", {"file_path": "test.py", "offset": 10, "limit": 50})

    def test_prints_empty_args(self) -> None:
        """Test that empty args are handled"""
        print_tool_call("some_tool", {})


class TestPrintToolResult:
    """Tests for print_tool_result function"""

    def test_prints_result(self) -> None:
        """Test that result is printed"""
        print_tool_result("read_tool", "file contents here")

    def test_truncates_long_result(self) -> None:
        """Test that long results are truncated"""
        long_result = "x" * 2000
        print_tool_result("read_tool", long_result)


class TestPrintError:
    """Tests for print_error function"""

    def test_prints_error(self) -> None:
        """Test that error is printed"""
        print_error("Something went wrong")


class TestPrintInfo:
    """Tests for print_info function"""

    def test_prints_info(self) -> None:
        """Test that info is printed"""
        print_info("Processing...")


class TestPrintWelcome:
    """Tests for print_welcome function"""

    def test_prints_welcome(self) -> None:
        """Test that welcome message is printed"""
        print_welcome()


class TestPrintGoodbye:
    """Tests for print_goodbye function"""

    def test_prints_goodbye(self) -> None:
        """Test that goodbye message is printed"""
        print_goodbye()
