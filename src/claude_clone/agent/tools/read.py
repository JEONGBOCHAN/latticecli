"""Read Tool - File reading with line numbers

Reads file contents with UTF-8 encoding and returns formatted output
with line numbers. Supports offset and limit for large files.

Usage:
    from claude_clone.agent.tools.read import read_tool

    # Use with LangGraph agent
    agent = create_agent(config, tools=[read_tool])
"""

from pathlib import Path

from langchain_core.tools import tool

from claude_clone.agent.tools.schemas import ReadInput


class ReadToolError(Exception):
    """Error during file read operation"""

    pass


class BinaryFileError(ReadToolError):
    """Attempted to read a binary file"""

    pass


class FileNotFoundError(ReadToolError):
    """File does not exist"""

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


def _is_binary(content: bytes) -> bool:
    """Check if content is binary by looking for null bytes

    Args:
        content: Raw file content (first 8192 bytes)

    Returns:
        True if binary file detected
    """
    return b"\x00" in content[:8192]


def _strip_bom(content: str) -> str:
    """Strip UTF-8 BOM if present

    Args:
        content: Decoded string content

    Returns:
        Content without BOM
    """
    if content.startswith("\ufeff"):
        return content[1:]
    return content


def _format_with_line_numbers(lines: list[str], start_line: int) -> str:
    """Format lines with line numbers

    Args:
        lines: List of lines to format
        start_line: Starting line number (1-based for display)

    Returns:
        Formatted string with line numbers

    Example output:
        1→def main():
        2→    print("hello")
    """
    result = []
    max_line_num = start_line + len(lines)
    width = len(str(max_line_num))

    for i, line in enumerate(lines):
        line_num = start_line + i
        # Remove trailing newline for consistent formatting
        line = line.rstrip("\n\r")
        result.append(f"{line_num:>{width}}→{line}")

    return "\n".join(result)


def read_file(file_path: str, offset: int = 0, limit: int = 2000) -> str:
    """Read file contents with line numbers

    Reads a file with UTF-8 encoding, applies offset and limit,
    and returns content with line numbers.

    Args:
        file_path: Path to file (absolute or relative)
        offset: Starting line number (0-based)
        limit: Maximum number of lines to read

    Returns:
        File content with line numbers

    Raises:
        FileNotFoundError: File does not exist
        BinaryFileError: File is binary
        ReadToolError: Other read errors
    """
    path = _normalize_path(file_path)

    # Check file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ReadToolError(f"Not a file: {path}")

    try:
        # Read raw bytes first to check for binary
        raw_content = path.read_bytes()

        if _is_binary(raw_content):
            raise BinaryFileError(f"Binary file cannot be read: {path}")

        # Decode with UTF-8, replace errors
        content = raw_content.decode("utf-8", errors="replace")
        content = _strip_bom(content)

        # Split into lines and apply offset/limit
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # Apply offset and limit
        selected_lines = lines[offset : offset + limit]

        if not selected_lines:
            return f"(Empty or offset beyond file. Total lines: {total_lines})"

        # Format with line numbers (1-based for display)
        start_line = offset + 1
        formatted = _format_with_line_numbers(selected_lines, start_line)

        # Add info if truncated
        end_line = offset + len(selected_lines)
        if end_line < total_lines:
            formatted += f"\n\n(Showing lines {start_line}-{end_line} of {total_lines})"

        return formatted

    except (BinaryFileError, FileNotFoundError):
        raise
    except Exception as e:
        raise ReadToolError(f"Failed to read file {path}: {e}") from e


@tool(args_schema=ReadInput)
def read_tool(file_path: str, offset: int = 0, limit: int = 2000) -> str:
    """Read the contents of a file with line numbers.

    Use this tool to read source code files, configuration files, or any text file.
    The output includes line numbers for easy reference.

    Args:
        file_path: Absolute path to the file to read
        offset: Starting line number (0-based, default: 0)
        limit: Maximum number of lines to read (default: 2000)

    Returns:
        File contents with line numbers, or error message
    """
    try:
        return read_file(file_path, offset, limit)
    except ReadToolError as e:
        return f"Error: {e}"
