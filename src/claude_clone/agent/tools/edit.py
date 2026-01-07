"""Edit Tool - File editing with string replacement

Replaces a specific string with a new string in an existing file.
Supports replacing first occurrence or all occurrences.

Usage:
    from claude_clone.agent.tools.edit import edit_tool

    # Use with LangGraph agent
    agent = create_agent(config, tools=[edit_tool])
"""

from pathlib import Path

from langchain_core.tools import tool

from claude_clone.agent.tools.schemas import EditInput


class EditToolError(Exception):
    """Error during file edit operation"""

    pass


class FileNotFoundError(EditToolError):
    """File does not exist"""

    pass


class StringNotFoundError(EditToolError):
    """Target string not found in file"""

    pass


class MultipleMatchesError(EditToolError):
    """Multiple matches found when replace_all=False"""

    pass


def _normalize_path(path: str) -> Path:
    """Normalize path to absolute path

    Args:
        path: File path (absolute or relative)

    Returns:
        Resolved absolute Path object
    """
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    """Edit file by replacing string

    Replaces occurrences of old_string with new_string in the file.

    Args:
        file_path: Path to file (absolute or relative)
        old_string: String to find and replace
        new_string: Replacement string
        replace_all: If True, replace all occurrences. If False, replace first only.

    Returns:
        Success message with number of replacements

    Raises:
        FileNotFoundError: File does not exist
        StringNotFoundError: old_string not found in file
        MultipleMatchesError: Multiple matches found when replace_all=False
        EditToolError: Other edit errors
    """
    path = _normalize_path(file_path)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise EditToolError(f"Not a file: {path}")

    try:
        # Read current content
        content = path.read_text(encoding="utf-8")

        # Check if old_string exists
        if old_string not in content:
            raise StringNotFoundError(
                f"String not found in file: {repr(old_string[:50])}..."
                if len(old_string) > 50
                else f"String not found in file: {repr(old_string)}"
            )

        # Count occurrences
        count = content.count(old_string)

        # Check for multiple matches when replace_all=False
        if not replace_all and count > 1:
            raise MultipleMatchesError(
                f"Found {count} occurrences of the string. "
                "Use replace_all=True to replace all, or provide a more specific string."
            )

        # Perform replacement
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replaced_count = count
        else:
            new_content = content.replace(old_string, new_string, 1)
            replaced_count = 1

        # Write back
        path.write_text(new_content, encoding="utf-8")

        # Return success message
        if replaced_count == 1:
            return f"Successfully replaced 1 occurrence in {path.name}"
        else:
            return f"Successfully replaced {replaced_count} occurrences in {path.name}"

    except (FileNotFoundError, StringNotFoundError, MultipleMatchesError):
        raise
    except Exception as e:
        raise EditToolError(f"Failed to edit file {path}: {e}") from e


@tool(args_schema=EditInput)
def edit_tool(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    """Edit a file by replacing a specific string.

    Use this tool to make targeted edits to existing files.
    The old_string must match exactly as it appears in the file.

    Args:
        file_path: Absolute path to the file to edit
        old_string: Exact string to find and replace
        new_string: New string to replace with
        replace_all: Replace all occurrences (default: False, first only)

    Returns:
        Success message or error description
    """
    try:
        return edit_file(file_path, old_string, new_string, replace_all)
    except EditToolError as e:
        return f"Error: {e}"
