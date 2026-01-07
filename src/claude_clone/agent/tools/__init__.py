"""Tools Module

Defines tools based on LangChain StructuredTool.
"""

from claude_clone.agent.tools.edit import (
    edit_file,
    edit_tool,
    EditToolError,
    MultipleMatchesError,
    StringNotFoundError,
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
]
