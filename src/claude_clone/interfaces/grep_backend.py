"""GrepBackend Interface - Code Search Abstraction

MVP: PythonGrep (pure Python)
Future: RipgrepGrep (ripgrep subprocess)
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class GrepMatch(BaseModel):
    """Single search result item"""

    file: str
    """File path (absolute)"""

    line: int
    """Line number (1-based)"""

    content: str
    """Matched line content"""

    context_before: list[str] = Field(default_factory=list)
    """Context lines before the match"""

    context_after: list[str] = Field(default_factory=list)
    """Context lines after the match"""


class GrepBackend(ABC):
    """Code search backend interface

    Implementations:
        - PythonGrep: Pure Python (re + pathlib) - MVP
        - RipgrepGrep: ripgrep subprocess call - Future
    """

    @abstractmethod
    def search(
        self,
        pattern: str,
        path: str = ".",
        *,
        file_type: str | None = None,
        context_lines: int = 0,
        max_results: int = 100,
        case_sensitive: bool | None = None,
    ) -> list[GrepMatch]:
        """Perform code search

        Args:
            pattern: Regex pattern to search for
            path: Search path (file or directory)
            file_type: File type filter (py, js, ts, etc.)
            context_lines: Number of context lines before/after
            max_results: Maximum number of results (protects LLM context)
            case_sensitive: Case sensitivity
                - True: Case sensitive
                - False: Case insensitive
                - None: Auto (True if pattern contains uppercase)

        Returns:
            List of search results (GrepMatch)

        Raises:
            FileNotFoundError: When path does not exist
            re.error: Invalid regex pattern
        """
        pass
