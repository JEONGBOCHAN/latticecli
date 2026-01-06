"""Tool Input Schemas (Pydantic)

Input schemas used with LangChain StructuredTool.
Defines parameters for each tool and ensures LLM calls them correctly.
"""

from pydantic import BaseModel, Field


class ReadInput(BaseModel):
    """Read file tool input"""

    file_path: str = Field(
        description="Absolute path to the file to read",
    )
    offset: int = Field(
        default=0,
        description="Starting line number (0-based)",
        ge=0,
    )
    limit: int = Field(
        default=2000,
        description="Maximum number of lines to read",
        ge=1,
        le=10000,
    )


class EditInput(BaseModel):
    """Edit file tool input

    Replaces a specific string with a new string in an existing file.
    The old_string must exist in the file.
    """

    file_path: str = Field(
        description="Absolute path to the file to edit",
    )
    old_string: str = Field(
        description="Existing string to replace (must match exactly)",
    )
    new_string: str = Field(
        description="New string to replace with",
    )
    replace_all: bool = Field(
        default=False,
        description="Replace all occurrences (default: first only)",
    )


class WriteInput(BaseModel):
    """Write file tool input

    Creates a new file or completely overwrites an existing file.
    For partial modifications, use the Edit tool.
    """

    file_path: str = Field(
        description="Absolute path to the file to write",
    )
    content: str = Field(
        description="Full content to write to the file",
    )


class BashInput(BaseModel):
    """Shell command execution tool input"""

    command: str = Field(
        description="Shell command to execute",
    )
    timeout: int = Field(
        default=120,
        description="Timeout in seconds",
        ge=1,
        le=600,
    )
    description: str = Field(
        default="",
        description="Command description (5-10 words)",
    )


class GrepInput(BaseModel):
    """Code search tool input"""

    pattern: str = Field(
        description="Regex pattern to search for",
    )
    path: str = Field(
        default=".",
        description="Directory or file path to search",
    )
    file_type: str | None = Field(
        default=None,
        description="File type filter (py, js, ts, etc.)",
    )
    context_lines: int = Field(
        default=0,
        description="Number of context lines before/after",
        ge=0,
        le=10,
    )
    max_results: int = Field(
        default=100,
        description="Maximum number of results",
        ge=1,
        le=1000,
    )


class GlobInput(BaseModel):
    """File pattern search tool input"""

    pattern: str = Field(
        description="Glob pattern (e.g., **/*.py, src/**/*.ts)",
    )
    path: str = Field(
        default=".",
        description="Starting directory for search",
    )
