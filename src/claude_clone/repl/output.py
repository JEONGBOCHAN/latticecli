"""Output Handler - Rich console output

Provides formatted output using Rich library.
Supports markdown rendering, code syntax highlighting, and styled messages.

Usage:
    from claude_clone.repl.output import print_response, print_error

    print_response("# Hello\\nThis is **markdown**")
    print_error("Something went wrong")
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

# Global console instance
_console: Console | None = None


def get_console() -> Console:
    """Get or create the global console instance

    Returns:
        The global Console instance
    """
    global _console
    if _console is None:
        _console = Console()
    return _console


def print_response(content: str) -> None:
    """Print AI response with markdown formatting

    Renders the content as markdown with:
        - Headers, bold, italic formatting
        - Code blocks with syntax highlighting
        - Lists and other markdown elements

    Args:
        content: Markdown-formatted response text
    """
    console = get_console()
    markdown = Markdown(content)
    console.print(markdown)


def print_tool_call(tool_name: str, tool_input: dict) -> None:  # type: ignore[type-arg]
    """Print tool call notification

    Displays a styled panel showing which tool is being called
    and with what arguments.

    Args:
        tool_name: Name of the tool being called
        tool_input: Dictionary of tool arguments
    """
    console = get_console()

    # Format tool input as key=value pairs
    args_str = ", ".join(f"{k}={repr(v)}" for k, v in tool_input.items())
    call_text = f"{tool_name}({args_str})"

    panel = Panel(
        Text(call_text, style="cyan"),
        title="[bold yellow]Tool Call[/bold yellow]",
        border_style="yellow",
    )
    console.print(panel)


def print_tool_result(tool_name: str, result: str) -> None:
    """Print tool execution result

    Displays the result of a tool call in a styled panel.

    Args:
        tool_name: Name of the tool that was called
        result: Result string from tool execution
    """
    console = get_console()

    # Truncate long results for display
    display_result = result
    if len(result) > 1000:
        display_result = result[:1000] + "\n... (truncated)"

    panel = Panel(
        display_result,
        title=f"[bold green]{tool_name} Result[/bold green]",
        border_style="green",
    )
    console.print(panel)


def print_error(message: str) -> None:
    """Print error message

    Displays an error message in red styling.

    Args:
        message: Error message to display
    """
    console = get_console()
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str) -> None:
    """Print info message

    Displays an informational message in dim styling.

    Args:
        message: Info message to display
    """
    console = get_console()
    console.print(f"[dim]{message}[/dim]")


def print_welcome() -> None:
    """Print welcome message

    Displays a welcome banner when the REPL starts.
    """
    console = get_console()
    console.print()
    console.print("[bold blue]Claude Clone[/bold blue] - AI Coding Assistant")
    console.print("[dim]Type your message and press Enter. Ctrl+C to cancel, Ctrl+D to exit.[/dim]")
    console.print()


def print_goodbye() -> None:
    """Print goodbye message

    Displays a farewell message when the REPL exits.
    """
    console = get_console()
    console.print()
    console.print("[dim]Goodbye![/dim]")


def reset_console() -> None:
    """Reset the console instance

    Clears the console state. Useful for testing.
    """
    global _console
    _console = None
