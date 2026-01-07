"""Bash Tool - Shell command execution

Executes shell commands and returns their output.
Supports timeout and captures both stdout and stderr.

Usage:
    from claude_clone.agent.tools.bash import bash_tool

    # Use with LangGraph agent
    agent = create_agent(config, tools=[bash_tool])
"""

import subprocess
import sys
from dataclasses import dataclass

from langchain_core.tools import tool

from claude_clone.agent.tools.schemas import BashInput


class BashToolError(Exception):
    """Error during bash command execution"""

    pass


class CommandTimeoutError(BashToolError):
    """Command execution timed out"""

    pass


class CommandExecutionError(BashToolError):
    """Command execution failed"""

    pass


@dataclass
class CommandResult:
    """Result of command execution"""

    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False


def run_command(
    command: str,
    timeout: int = 120,
    cwd: str | None = None,
) -> CommandResult:
    """Execute a shell command

    Runs the command in a subprocess and captures output.

    Args:
        command: Shell command to execute
        timeout: Maximum execution time in seconds (default: 120)
        cwd: Working directory for command execution (default: current directory)

    Returns:
        CommandResult with stdout, stderr, return_code, and timed_out flag

    Raises:
        CommandTimeoutError: If command exceeds timeout
        CommandExecutionError: If command cannot be started
        BashToolError: Other execution errors
    """
    # Determine shell based on platform
    if sys.platform == "win32":
        shell_cmd = ["cmd", "/c", command]
    else:
        shell_cmd = ["bash", "-c", command]

    try:
        process = subprocess.run(
            shell_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        return CommandResult(
            stdout=process.stdout,
            stderr=process.stderr,
            return_code=process.returncode,
            timed_out=False,
        )

    except subprocess.TimeoutExpired as e:
        # Return partial output if available
        # Note: stdout/stderr are strings when text=True, bytes otherwise
        if e.stdout:
            stdout = e.stdout if isinstance(e.stdout, str) else e.stdout.decode("utf-8", errors="replace")
        else:
            stdout = ""

        raise CommandTimeoutError(
            f"Command timed out after {timeout} seconds. "
            f"Partial output: {stdout[:500] if stdout else '(none)'}"
        ) from e

    except FileNotFoundError as e:
        raise CommandExecutionError(
            f"Shell not found. Command: {command[:50]}..."
            if len(command) > 50
            else f"Shell not found. Command: {command}"
        ) from e

    except Exception as e:
        raise BashToolError(f"Failed to execute command: {e}") from e


def format_output(result: CommandResult, max_length: int = 10000) -> str:
    """Format command result for display

    Args:
        result: CommandResult from run_command
        max_length: Maximum output length before truncation

    Returns:
        Formatted output string
    """
    parts = []

    # Add stdout if present
    if result.stdout:
        stdout = result.stdout
        if len(stdout) > max_length:
            stdout = stdout[:max_length] + f"\n... (truncated, {len(result.stdout)} total chars)"
        parts.append(stdout)

    # Add stderr if present
    if result.stderr:
        stderr = result.stderr
        if len(stderr) > max_length:
            stderr = stderr[:max_length] + f"\n... (truncated, {len(result.stderr)} total chars)"
        parts.append(f"STDERR:\n{stderr}")

    # Handle empty output
    if not parts:
        if result.return_code == 0:
            return "(no output)"
        else:
            return f"(no output, exit code: {result.return_code})"

    output = "\n".join(parts)

    # Add exit code if non-zero
    if result.return_code != 0:
        output += f"\n\nExit code: {result.return_code}"

    return output


@tool(args_schema=BashInput)
def bash_tool(
    command: str,
    timeout: int = 120,
    description: str = "",
) -> str:
    """Execute a shell command.

    Use this tool to run shell commands like git, npm, pip, etc.
    Commands are executed in the current working directory.

    Args:
        command: Shell command to execute
        timeout: Maximum execution time in seconds (default: 120, max: 600)
        description: Brief description of what the command does (5-10 words)

    Returns:
        Command output (stdout and stderr) or error message
    """
    try:
        result = run_command(command, timeout=timeout)
        return format_output(result)
    except BashToolError as e:
        return f"Error: {e}"
