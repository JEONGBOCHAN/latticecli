"""Grep Tool - Code/text search with regex

Searches for patterns in files using regular expressions.
Pure Python implementation (ripgrep backend can be added later).

Usage:
    from claude_clone.agent.tools.grep import grep_tool

    # Use with LangGraph agent
    agent = create_agent(config, tools=[grep_tool])
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.tools import tool

from claude_clone.agent.tools.schemas import GrepInput


class GrepToolError(Exception):
    """Error during grep operation"""

    pass


class InvalidPatternError(GrepToolError):
    """Invalid regex pattern"""

    pass


class PathNotFoundError(GrepToolError):
    """Path does not exist"""

    pass


# File type to extension mapping
FILE_TYPE_EXTENSIONS: dict[str, list[str]] = {
    "py": [".py", ".pyi"],
    "js": [".js", ".mjs", ".cjs"],
    "ts": [".ts", ".tsx"],
    "jsx": [".jsx"],
    "java": [".java"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh"],
    "go": [".go"],
    "rs": [".rs"],
    "rb": [".rb"],
    "php": [".php"],
    "swift": [".swift"],
    "kt": [".kt", ".kts"],
    "scala": [".scala"],
    "cs": [".cs"],
    "md": [".md", ".markdown"],
    "json": [".json"],
    "yaml": [".yaml", ".yml"],
    "toml": [".toml"],
    "xml": [".xml"],
    "html": [".html", ".htm"],
    "css": [".css", ".scss", ".sass", ".less"],
    "sql": [".sql"],
    "sh": [".sh", ".bash", ".zsh"],
}


@dataclass
class GrepMatch:
    """A single grep match"""

    file: str
    line_number: int
    content: str
    context_before: list[str] = field(default_factory=list)
    context_after: list[str] = field(default_factory=list)


def _normalize_path(path: str) -> Path:
    """Normalize path to absolute path"""
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


def _get_extensions_for_type(file_type: str) -> list[str]:
    """Get file extensions for a given type"""
    return FILE_TYPE_EXTENSIONS.get(file_type.lower(), [f".{file_type}"])


def _should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped (binary, too large, etc.)"""
    # Skip hidden files and directories
    if any(part.startswith(".") for part in file_path.parts):
        return True

    # Skip common non-text directories
    skip_dirs = {"node_modules", "__pycache__", ".git", ".venv", "venv", "dist", "build"}
    if any(part in skip_dirs for part in file_path.parts):
        return True

    # Skip files larger than 1MB
    try:
        if file_path.stat().st_size > 1_000_000:
            return True
    except OSError:
        return True

    return False


def _is_binary_file(file_path: Path) -> bool:
    """Quick check if file appears to be binary"""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            # Check for null bytes (common in binary files)
            if b"\x00" in chunk:
                return True
    except OSError:
        return True
    return False


def grep_files(
    pattern: str,
    path: str = ".",
    file_type: str | None = None,
    context_lines: int = 0,
    max_results: int = 100,
) -> list[GrepMatch]:
    """Search for pattern in files

    Args:
        pattern: Regex pattern to search for
        path: Directory or file to search in
        file_type: Filter by file type (py, js, ts, etc.)
        context_lines: Number of context lines before/after match
        max_results: Maximum number of matches to return

    Returns:
        List of GrepMatch objects

    Raises:
        InvalidPatternError: If pattern is not valid regex
        PathNotFoundError: If path does not exist
        GrepToolError: Other grep errors
    """
    # Validate and compile pattern
    try:
        regex = re.compile(pattern)
    except re.error as e:
        raise InvalidPatternError(f"Invalid regex pattern: {e}") from e

    search_path = _normalize_path(path)

    if not search_path.exists():
        raise PathNotFoundError(f"Path not found: {search_path}")

    # Get file extensions filter
    extensions = _get_extensions_for_type(file_type) if file_type else None

    matches: list[GrepMatch] = []

    try:
        # Get list of files to search
        if search_path.is_file():
            files = [search_path]
        else:
            files = list(search_path.rglob("*"))

        for file_path in files:
            if len(matches) >= max_results:
                break

            if not file_path.is_file():
                continue

            # Apply file type filter
            if extensions and file_path.suffix.lower() not in extensions:
                continue

            # Skip binary and large files
            if _should_skip_file(file_path):
                continue

            if _is_binary_file(file_path):
                continue

            # Search file
            try:
                file_matches = _search_file(
                    file_path, regex, context_lines, max_results - len(matches), search_path
                )
                matches.extend(file_matches)
            except (OSError, UnicodeDecodeError):
                # Skip files that can't be read
                continue

    except Exception as e:
        raise GrepToolError(f"Grep search failed: {e}") from e

    return matches


def _search_file(
    file_path: Path,
    regex: re.Pattern[str],
    context_lines: int,
    max_matches: int,
    base_path: Path,
) -> list[GrepMatch]:
    """Search a single file for pattern matches"""
    matches: list[GrepMatch] = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    lines = content.splitlines()

    for i, line in enumerate(lines):
        if len(matches) >= max_matches:
            break

        if regex.search(line):
            # Get relative path
            try:
                rel_path = str(file_path.relative_to(base_path))
            except ValueError:
                rel_path = str(file_path)

            # Get context lines
            context_before = []
            context_after = []

            if context_lines > 0:
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context_before = lines[start:i]
                context_after = lines[i + 1 : end]

            matches.append(
                GrepMatch(
                    file=rel_path,
                    line_number=i + 1,  # 1-based line numbers
                    content=line,
                    context_before=context_before,
                    context_after=context_after,
                )
            )

    return matches


def format_grep_results(
    matches: list[GrepMatch],
    max_results: int = 100,
    show_context: bool = True,
) -> str:
    """Format grep results for display

    Args:
        matches: List of GrepMatch objects
        max_results: Maximum results that were requested
        show_context: Whether to show context lines

    Returns:
        Formatted string with matches
    """
    if not matches:
        return "No matches found."

    parts = [f"Found {len(matches)} match(es):\n"]

    for match in matches:
        # Format: file:line: content
        header = f"{match.file}:{match.line_number}:"

        if show_context and match.context_before:
            for ctx_line in match.context_before:
                parts.append(f"  {ctx_line}")

        parts.append(f"{header} {match.content}")

        if show_context and match.context_after:
            for ctx_line in match.context_after:
                parts.append(f"  {ctx_line}")

        if show_context and (match.context_before or match.context_after):
            parts.append("")  # Empty line between matches with context

    if len(matches) >= max_results:
        parts.append(f"\n(Results limited to {max_results})")

    return "\n".join(parts)


@tool(args_schema=GrepInput)
def grep_tool(
    pattern: str,
    path: str = ".",
    file_type: str | None = None,
    context_lines: int = 0,
    max_results: int = 100,
) -> str:
    """Search for a pattern in files using regex.

    Use this tool to find code or text patterns across files.
    Supports regex patterns and file type filtering.

    Args:
        pattern: Regex pattern to search for
        path: Directory or file to search (default: current directory)
        file_type: Filter by file type (py, js, ts, etc.)
        context_lines: Number of context lines before/after match (0-10)
        max_results: Maximum number of results (default: 100)

    Returns:
        List of matches with file paths and line numbers, or error message
    """
    try:
        matches = grep_files(pattern, path, file_type, context_lines, max_results)
        return format_grep_results(matches, max_results, show_context=context_lines > 0)
    except GrepToolError as e:
        return f"Error: {e}"
