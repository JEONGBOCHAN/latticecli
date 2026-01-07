"""System Prompts for Claude Clone Agent

Provides system prompts that define agent behavior and tool usage.
The prompts are designed to be modular and extensible for future tools.

Usage:
    from claude_clone.prompts import get_system_prompt

    prompt = get_system_prompt()
    # Use as SystemMessage in LangGraph agent
"""

# Base system prompt defining the agent's role and behavior
_BASE_PROMPT = """You are an AI coding assistant that helps developers with software engineering tasks.

Your primary capabilities include:
- Reading and understanding source code files
- Answering questions about code structure and logic
- Helping debug issues and suggesting improvements
- Explaining code functionality

Guidelines:
- Always read files before making suggestions about them
- Provide clear, concise explanations
- When showing code, include relevant context
- Be honest when you're uncertain about something"""


# Tool-specific instructions
_READ_TOOL_PROMPT = """
## Read Tool

Use the read_tool to read file contents. The tool returns file content with line numbers.

When to use:
- When asked to read, view, or show a file
- Before answering questions about specific file contents
- To understand code structure before making suggestions

Parameters:
- file_path: Path to the file (absolute or relative)
- offset: Starting line number (0-based, default: 0)
- limit: Maximum lines to read (default: 2000)

Example usage patterns:
- "Show me main.py" -> Use read_tool with file_path="main.py"
- "Read lines 50-100 of config.py" -> Use read_tool with offset=49, limit=51"""


# Language instruction
_LANGUAGE_PROMPT = """
## Response Language

Respond in Korean (한국어) unless the user explicitly requests another language."""


def get_system_prompt(include_tools: bool = True) -> str:
    """Get the complete system prompt

    Assembles the system prompt from modular components.
    This design allows easy extension as new tools are added.

    Args:
        include_tools: Whether to include tool usage instructions.
                      Set to False for simple chat without tools.

    Returns:
        Complete system prompt string

    Example:
        >>> prompt = get_system_prompt()
        >>> len(prompt) > 0
        True
        >>> "AI coding assistant" in prompt
        True
    """
    parts = [_BASE_PROMPT]

    if include_tools:
        parts.append(_READ_TOOL_PROMPT)

    parts.append(_LANGUAGE_PROMPT)

    return "\n".join(parts)


def get_tool_instructions(tool_name: str) -> str | None:
    """Get instructions for a specific tool

    Useful for dynamically building prompts based on available tools.

    Args:
        tool_name: Name of the tool (e.g., "read", "edit", "bash")

    Returns:
        Tool instruction string, or None if tool not found

    Example:
        >>> instructions = get_tool_instructions("read")
        >>> "read_tool" in instructions
        True
        >>> get_tool_instructions("unknown") is None
        True
    """
    tool_prompts = {
        "read": _READ_TOOL_PROMPT,
        # Future tools will be added here:
        # "edit": _EDIT_TOOL_PROMPT,
        # "bash": _BASH_TOOL_PROMPT,
        # "glob": _GLOB_TOOL_PROMPT,
        # "grep": _GREP_TOOL_PROMPT,
    }

    return tool_prompts.get(tool_name)


# Convenience constant for direct import
SYSTEM_PROMPT = get_system_prompt()
