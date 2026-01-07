"""Prompts Module

System prompts and tool instructions for the Claude Clone agent.
"""

from claude_clone.prompts.system import (
    SYSTEM_PROMPT,
    get_system_prompt,
    get_tool_instructions,
)

__all__ = [
    "SYSTEM_PROMPT",
    "get_system_prompt",
    "get_tool_instructions",
]
