"""Tests for System Prompt"""

import pytest

from claude_clone.prompts import (
    SYSTEM_PROMPT,
    get_system_prompt,
    get_tool_instructions,
)


class TestGetSystemPrompt:
    """Tests for get_system_prompt function"""

    def test_returns_non_empty_string(self) -> None:
        """Test that prompt is returned"""
        prompt = get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_contains_assistant_role(self) -> None:
        """Test that prompt defines assistant role"""
        prompt = get_system_prompt()

        assert "AI coding assistant" in prompt

    def test_contains_read_tool_instructions(self) -> None:
        """Test that prompt includes read tool instructions by default"""
        prompt = get_system_prompt()

        assert "read_tool" in prompt
        assert "file_path" in prompt

    def test_contains_korean_language_instruction(self) -> None:
        """Test that prompt specifies Korean response language"""
        prompt = get_system_prompt()

        assert "Korean" in prompt or "한국어" in prompt

    def test_without_tools(self) -> None:
        """Test prompt without tool instructions"""
        prompt = get_system_prompt(include_tools=False)

        assert "AI coding assistant" in prompt
        assert "read_tool" not in prompt

    def test_with_tools(self) -> None:
        """Test prompt with tool instructions (default)"""
        prompt = get_system_prompt(include_tools=True)

        assert "Read Tool" in prompt
        assert "read_tool" in prompt


class TestGetToolInstructions:
    """Tests for get_tool_instructions function"""

    def test_read_tool_instructions(self) -> None:
        """Test getting read tool instructions"""
        instructions = get_tool_instructions("read")

        assert instructions is not None
        assert "read_tool" in instructions
        assert "file_path" in instructions

    def test_unknown_tool_returns_none(self) -> None:
        """Test that unknown tool returns None"""
        result = get_tool_instructions("unknown_tool")

        assert result is None

    def test_case_sensitive(self) -> None:
        """Test that tool name is case sensitive"""
        result = get_tool_instructions("READ")

        assert result is None


class TestSystemPromptConstant:
    """Tests for SYSTEM_PROMPT constant"""

    def test_constant_exists(self) -> None:
        """Test that SYSTEM_PROMPT constant is available"""
        assert SYSTEM_PROMPT is not None
        assert isinstance(SYSTEM_PROMPT, str)

    def test_constant_matches_function(self) -> None:
        """Test that constant matches function output"""
        assert SYSTEM_PROMPT == get_system_prompt()

    def test_constant_includes_tools(self) -> None:
        """Test that constant includes tool instructions"""
        assert "read_tool" in SYSTEM_PROMPT
