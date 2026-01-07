"""Input Handler - User input using prompt_toolkit

Provides a multi-line input interface with editing capabilities.
Uses prompt_toolkit for rich input experience.

Usage:
    from claude_clone.repl.input import get_user_input

    user_input = get_user_input()
"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


def create_key_bindings() -> KeyBindings:
    """Create custom key bindings for input

    Bindings:
        - Enter: Submit single-line input
        - Alt+Enter or Esc+Enter: Insert newline for multi-line input
        - Ctrl+C: Cancel current input
        - Ctrl+D: Exit application

    Returns:
        KeyBindings object with custom bindings
    """
    bindings = KeyBindings()

    @bindings.add(Keys.Escape, Keys.Enter)
    def _insert_newline(event) -> None:  # type: ignore[no-untyped-def]
        """Alt+Enter or Esc+Enter inserts newline for multi-line input"""
        event.current_buffer.insert_text("\n")

    return bindings


def create_prompt_session() -> PromptSession[str]:
    """Create a configured prompt session

    Creates a prompt session with:
        - In-memory history for up/down arrow navigation
        - Custom key bindings for multi-line input
        - Multi-line mode enabled

    Returns:
        Configured PromptSession
    """
    history = InMemoryHistory()
    key_bindings = create_key_bindings()

    return PromptSession(
        history=history,
        key_bindings=key_bindings,
        multiline=False,  # Single line by default, Esc+Enter for multi-line
    )


# Global session for reuse across calls
_session: PromptSession[str] | None = None


def get_prompt_session() -> PromptSession[str]:
    """Get or create the global prompt session

    Returns:
        The global PromptSession instance
    """
    global _session
    if _session is None:
        _session = create_prompt_session()
    return _session


def get_user_input(prompt: str = "> ") -> str:
    """Get user input using prompt_toolkit

    Provides a rich input experience with:
        - Command history (up/down arrows)
        - Line editing (left/right, backspace, delete)
        - Multi-line input support (Esc+Enter)

    Args:
        prompt: The prompt string to display (default: "> ")

    Returns:
        User input string (stripped of leading/trailing whitespace)

    Raises:
        EOFError: When user presses Ctrl+D
        KeyboardInterrupt: When user presses Ctrl+C
    """
    session = get_prompt_session()
    user_input = session.prompt(prompt)
    return user_input.strip()


def reset_session() -> None:
    """Reset the prompt session

    Clears the session state. Useful for testing.
    """
    global _session
    _session = None
