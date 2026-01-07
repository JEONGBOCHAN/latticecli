"""Tests for Edit Tool"""

from pathlib import Path

import pytest

from claude_clone.agent.tools.edit import (
    EditToolError,
    FileNotFoundError,
    MultipleMatchesError,
    StringNotFoundError,
    edit_file,
    edit_tool,
)


class TestEditFile:
    """Tests for edit_file function"""

    def test_replace_single_occurrence(self, tmp_path: Path) -> None:
        """Test replacing a single occurrence"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n", encoding="utf-8")

        result = edit_file(str(test_file), "hello", "goodbye")

        assert "Successfully replaced 1 occurrence" in result
        assert test_file.read_text(encoding="utf-8") == "goodbye world\n"

    def test_replace_multiline_string(self, tmp_path: Path) -> None:
        """Test replacing a multiline string"""
        test_file = tmp_path / "test.txt"
        original = "line 1\nline 2\nline 3\n"
        test_file.write_text(original, encoding="utf-8")

        result = edit_file(str(test_file), "line 2\nline 3", "replaced")

        assert "Successfully replaced 1 occurrence" in result
        assert test_file.read_text(encoding="utf-8") == "line 1\nreplaced\n"

    def test_replace_all_occurrences(self, tmp_path: Path) -> None:
        """Test replacing all occurrences with replace_all=True"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("foo bar foo baz foo\n", encoding="utf-8")

        result = edit_file(str(test_file), "foo", "qux", replace_all=True)

        assert "Successfully replaced 3 occurrences" in result
        assert test_file.read_text(encoding="utf-8") == "qux bar qux baz qux\n"

    def test_multiple_matches_without_replace_all_raises(self, tmp_path: Path) -> None:
        """Test that multiple matches without replace_all raises error"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("foo bar foo\n", encoding="utf-8")

        with pytest.raises(MultipleMatchesError) as exc_info:
            edit_file(str(test_file), "foo", "baz")

        assert "Found 2 occurrences" in str(exc_info.value)
        assert "replace_all=True" in str(exc_info.value)
        # File should remain unchanged
        assert test_file.read_text(encoding="utf-8") == "foo bar foo\n"

    def test_string_not_found_raises(self, tmp_path: Path) -> None:
        """Test that missing string raises error"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n", encoding="utf-8")

        with pytest.raises(StringNotFoundError) as exc_info:
            edit_file(str(test_file), "goodbye", "farewell")

        assert "String not found" in str(exc_info.value)

    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        """Test that nonexistent file raises error"""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError) as exc_info:
            edit_file(str(nonexistent), "hello", "goodbye")

        assert "File not found" in str(exc_info.value)

    def test_replace_with_empty_string(self, tmp_path: Path) -> None:
        """Test replacing with empty string (deletion)"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n", encoding="utf-8")

        result = edit_file(str(test_file), " world", "")

        assert "Successfully replaced 1 occurrence" in result
        assert test_file.read_text(encoding="utf-8") == "hello\n"

    def test_replace_preserves_encoding(self, tmp_path: Path) -> None:
        """Test that UTF-8 content is preserved"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("안녕하세요 world\n", encoding="utf-8")

        result = edit_file(str(test_file), "world", "세계")

        assert "Successfully replaced 1 occurrence" in result
        assert test_file.read_text(encoding="utf-8") == "안녕하세요 세계\n"

    def test_replace_relative_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test editing with relative path"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n", encoding="utf-8")

        monkeypatch.chdir(tmp_path)

        result = edit_file("test.txt", "hello", "goodbye")

        assert "Successfully replaced 1 occurrence" in result
        assert test_file.read_text(encoding="utf-8") == "goodbye world\n"

    def test_edit_directory_raises_error(self, tmp_path: Path) -> None:
        """Test that editing a directory raises error"""
        with pytest.raises(EditToolError) as exc_info:
            edit_file(str(tmp_path), "hello", "goodbye")

        assert "Not a file" in str(exc_info.value)

    def test_string_not_found_truncates_long_string(self, tmp_path: Path) -> None:
        """Test that long missing strings are truncated in error"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("short content\n", encoding="utf-8")

        long_string = "a" * 100

        with pytest.raises(StringNotFoundError) as exc_info:
            edit_file(str(test_file), long_string, "replacement")

        error_msg = str(exc_info.value)
        assert "..." in error_msg
        assert len(error_msg) < 150  # Truncated reasonably


class TestEditTool:
    """Tests for edit_tool LangChain tool"""

    def test_tool_returns_success(self, tmp_path: Path) -> None:
        """Test that tool returns success message"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n", encoding="utf-8")

        result = edit_tool.invoke(
            {
                "file_path": str(test_file),
                "old_string": "hello",
                "new_string": "goodbye",
            }
        )

        assert "Successfully replaced" in result

    def test_tool_returns_error_message(self, tmp_path: Path) -> None:
        """Test that tool returns error message instead of raising"""
        nonexistent = tmp_path / "nonexistent.txt"

        result = edit_tool.invoke(
            {
                "file_path": str(nonexistent),
                "old_string": "hello",
                "new_string": "goodbye",
            }
        )

        assert "Error:" in result
        assert "File not found" in result

    def test_tool_returns_multiple_matches_error(self, tmp_path: Path) -> None:
        """Test that tool returns error for multiple matches"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("foo bar foo\n", encoding="utf-8")

        result = edit_tool.invoke(
            {
                "file_path": str(test_file),
                "old_string": "foo",
                "new_string": "baz",
            }
        )

        assert "Error:" in result
        assert "occurrences" in result

    def test_tool_has_correct_name(self) -> None:
        """Test that tool has the expected name"""
        assert edit_tool.name == "edit_tool"

    def test_tool_has_description(self) -> None:
        """Test that tool has a description"""
        assert edit_tool.description is not None
        assert len(edit_tool.description) > 0

    def test_tool_with_replace_all(self, tmp_path: Path) -> None:
        """Test that tool supports replace_all parameter"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("foo bar foo\n", encoding="utf-8")

        result = edit_tool.invoke(
            {
                "file_path": str(test_file),
                "old_string": "foo",
                "new_string": "baz",
                "replace_all": True,
            }
        )

        assert "Successfully replaced 2 occurrences" in result
        assert test_file.read_text(encoding="utf-8") == "baz bar baz\n"
