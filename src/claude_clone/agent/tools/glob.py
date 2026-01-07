"""Glob Tool - File pattern matching

Searches for files matching glob patterns (e.g., **/*.py).
Returns list of matching file paths.

Usage:
    from claude_clone.agent.tools.glob import glob_tool

    # Use with LangGraph agent
    agent = create_agent(config, tools=[glob_tool])
"""

from pathlib import Path

from langchain_core.tools import tool

from claude_clone.agent.tools.schemas import GlobInput


class GlobToolError(Exception):
    """Error during glob operation"""

    pass


class DirectoryNotFoundError(GlobToolError):
    """Directory does not exist"""

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


def glob_files(
    pattern: str,
    path: str = ".",
    max_results: int = 1000,
) -> list[str]:
    """Search for files matching glob pattern

    Args:
        pattern: Glob pattern (e.g., **/*.py, src/**/*.ts)
        path: Starting directory for search (default: current directory)
        max_results: Maximum number of results to return

    Returns:
        List of matching file paths (relative to search path)

    Raises:
        DirectoryNotFoundError: If path does not exist
        GlobToolError: Other glob errors
    """
    search_path = _normalize_path(path)

    if not search_path.exists():
        raise DirectoryNotFoundError(f"Directory not found: {search_path}")

    if not search_path.is_dir():
        raise GlobToolError(f"Not a directory: {search_path}")

    try:
        matches = []
        for match in search_path.glob(pattern):
            if match.is_file():
                # Return relative path from search directory
                try:
                    rel_path = match.relative_to(search_path)
                    matches.append(str(rel_path))
                except ValueError:
                    # If relative_to fails, use absolute path
                    matches.append(str(match))

            if len(matches) >= max_results:
                break

        # Sort for consistent output
        matches.sort()
        return matches

    except Exception as e:
        raise GlobToolError(f"Glob search failed: {e}") from e


def format_glob_results(matches: list[str], max_results: int = 1000) -> str:
    """Format glob results for display

    Args:
        matches: List of matching file paths
        max_results: Maximum results that were requested

    Returns:
        Formatted string with matches
    """
    if not matches:
        return "No files found matching pattern."

    result = f"Found {len(matches)} file(s):\n"
    result += "\n".join(matches)

    if len(matches) >= max_results:
        result += f"\n\n(Results limited to {max_results})"

    return result


@tool(args_schema=GlobInput)
def glob_tool(
    pattern: str,
    path: str = ".",
) -> str:
    """Search for files matching a glob pattern.

    Use this tool to find files by pattern (e.g., **/*.py for all Python files).
    Returns a list of matching file paths.

    Args:
        pattern: Glob pattern (e.g., **/*.py, src/**/*.ts, *.md)
        path: Starting directory for search (default: current directory)

    Returns:
        List of matching files or error message
    """
    try:
        matches = glob_files(pattern, path)
        return format_glob_results(matches)
    except GlobToolError as e:
        return f"Error: {e}"
