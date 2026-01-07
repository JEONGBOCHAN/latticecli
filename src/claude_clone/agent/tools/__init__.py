"""Tools Module

Defines tools based on LangChain StructuredTool.
"""

from claude_clone.agent.tools.bash import (
    bash_tool,
    BashToolError,
    CommandExecutionError,
    CommandResult,
    CommandTimeoutError,
    run_command,
)
from claude_clone.agent.tools.edit import (
    edit_file,
    edit_tool,
    EditToolError,
    MultipleMatchesError,
    StringNotFoundError,
)
from claude_clone.agent.tools.glob import (
    glob_files,
    glob_tool,
    GlobToolError,
)
from claude_clone.agent.tools.grep import (
    grep_files,
    grep_tool,
    GrepMatch,
    GrepToolError,
    InvalidPatternError,
)
from claude_clone.agent.tools.read import (
    BinaryFileError,
    read_file,
    read_tool,
    ReadToolError,
)
from claude_clone.agent.tools.schemas import (
    BashInput,
    EditInput,
    GlobInput,
    GrepInput,
    ReadInput,
    WriteInput,
)

# Note: FileNotFoundError is intentionally not exported as it shadows the builtin.
# Use EditToolError or ReadToolError for error handling.

__all__ = [
    # Schemas
    "ReadInput",
    "EditInput",
    "WriteInput",
    "BashInput",
    "GrepInput",
    "GlobInput",
    # Read tool
    "read_tool",
    "read_file",
    "ReadToolError",
    "BinaryFileError",
    # Edit tool
    "edit_tool",
    "edit_file",
    "EditToolError",
    "StringNotFoundError",
    "MultipleMatchesError",
    # Bash tool
    "bash_tool",
    "run_command",
    "CommandResult",
    "BashToolError",
    "CommandTimeoutError",
    "CommandExecutionError",
    # Glob tool
    "glob_tool",
    "glob_files",
    "GlobToolError",
    # Grep tool
    "grep_tool",
    "grep_files",
    "GrepMatch",
    "GrepToolError",
    "InvalidPatternError",
]
