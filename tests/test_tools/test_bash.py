"""Tests for Bash Tool"""

import sys

import pytest

from claude_clone.agent.tools.bash import (
    BashToolError,
    CommandResult,
    CommandTimeoutError,
    bash_tool,
    format_output,
    run_command,
)


class TestRunCommand:
    """Tests for run_command function"""

    def test_simple_echo(self) -> None:
        """Test simple echo command"""
        if sys.platform == "win32":
            result = run_command("echo hello")
        else:
            result = run_command("echo hello")

        assert result.return_code == 0
        assert "hello" in result.stdout
        assert result.timed_out is False

    def test_command_with_exit_code(self) -> None:
        """Test command that returns non-zero exit code"""
        if sys.platform == "win32":
            result = run_command("cmd /c exit 1")
        else:
            result = run_command("exit 1")

        assert result.return_code == 1
        assert result.timed_out is False

    def test_command_with_stderr(self) -> None:
        """Test command that writes to stderr"""
        if sys.platform == "win32":
            # Windows: redirect to stderr
            result = run_command("echo error 1>&2")
        else:
            result = run_command("echo error >&2")

        assert "error" in result.stderr or "error" in result.stdout

    def test_command_timeout(self) -> None:
        """Test that long commands timeout"""
        if sys.platform == "win32":
            cmd = "ping -n 10 127.0.0.1"
        else:
            cmd = "sleep 10"

        with pytest.raises(CommandTimeoutError) as exc_info:
            run_command(cmd, timeout=1)

        assert "timed out" in str(exc_info.value)

    def test_multiline_output(self) -> None:
        """Test command with multiline output"""
        if sys.platform == "win32":
            result = run_command("echo line1 & echo line2")
        else:
            result = run_command("echo 'line1'; echo 'line2'")

        assert "line1" in result.stdout
        assert "line2" in result.stdout

    def test_command_with_pipe(self) -> None:
        """Test command with pipe"""
        if sys.platform == "win32":
            result = run_command("echo hello world | findstr world")
        else:
            result = run_command("echo 'hello world' | grep world")

        assert "world" in result.stdout
        assert result.return_code == 0

    def test_python_command(self) -> None:
        """Test running python command"""
        if sys.platform == "win32":
            # Windows cmd.exe needs different quoting
            result = run_command("python -c print(1+1)")
        else:
            result = run_command('python -c "print(1+1)"')

        assert "2" in result.stdout
        assert result.return_code == 0


class TestFormatOutput:
    """Tests for format_output function"""

    def test_format_stdout_only(self) -> None:
        """Test formatting stdout only"""
        result = CommandResult(stdout="hello\n", stderr="", return_code=0)
        output = format_output(result)

        assert "hello" in output
        assert "STDERR" not in output

    def test_format_stderr_included(self) -> None:
        """Test formatting includes stderr"""
        result = CommandResult(stdout="out\n", stderr="err\n", return_code=0)
        output = format_output(result)

        assert "out" in output
        assert "STDERR:" in output
        assert "err" in output

    def test_format_empty_output_success(self) -> None:
        """Test formatting empty output with success"""
        result = CommandResult(stdout="", stderr="", return_code=0)
        output = format_output(result)

        assert "(no output)" in output

    def test_format_empty_output_failure(self) -> None:
        """Test formatting empty output with failure"""
        result = CommandResult(stdout="", stderr="", return_code=1)
        output = format_output(result)

        assert "exit code: 1" in output

    def test_format_nonzero_exit_code(self) -> None:
        """Test formatting includes exit code when non-zero"""
        result = CommandResult(stdout="output\n", stderr="", return_code=42)
        output = format_output(result)

        assert "output" in output
        assert "Exit code: 42" in output

    def test_format_truncates_long_output(self) -> None:
        """Test that long output is truncated"""
        long_output = "x" * 20000
        result = CommandResult(stdout=long_output, stderr="", return_code=0)
        output = format_output(result, max_length=1000)

        assert len(output) < 15000  # Truncated
        assert "truncated" in output

    def test_format_truncates_long_stderr(self) -> None:
        """Test that long stderr is truncated"""
        long_stderr = "e" * 20000
        result = CommandResult(stdout="", stderr=long_stderr, return_code=1)
        output = format_output(result, max_length=1000)

        assert "truncated" in output


class TestBashTool:
    """Tests for bash_tool LangChain tool"""

    def test_tool_returns_output(self) -> None:
        """Test that tool returns command output"""
        if sys.platform == "win32":
            result = bash_tool.invoke({"command": "echo hello", "timeout": 30})
        else:
            result = bash_tool.invoke({"command": "echo hello", "timeout": 30})

        assert "hello" in result

    def test_tool_returns_error_on_timeout(self) -> None:
        """Test that tool returns error message on timeout"""
        if sys.platform == "win32":
            cmd = "ping -n 10 127.0.0.1"
        else:
            cmd = "sleep 10"

        result = bash_tool.invoke({"command": cmd, "timeout": 1})

        assert "Error:" in result
        assert "timed out" in result

    def test_tool_has_correct_name(self) -> None:
        """Test that tool has the expected name"""
        assert bash_tool.name == "bash_tool"

    def test_tool_has_description(self) -> None:
        """Test that tool has a description"""
        assert bash_tool.description is not None
        assert len(bash_tool.description) > 0

    def test_tool_with_description_param(self) -> None:
        """Test that description parameter is accepted"""
        result = bash_tool.invoke({
            "command": "echo test",
            "timeout": 30,
            "description": "Print test message",
        })

        assert "test" in result

    def test_tool_default_timeout(self) -> None:
        """Test that default timeout works"""
        result = bash_tool.invoke({"command": "echo fast"})

        assert "fast" in result
