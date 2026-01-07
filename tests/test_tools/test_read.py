"""Tests for Read Tool"""

from pathlib import Path

import pytest

from claude_clone.agent.tools.read import (
    BinaryFileError,
    FileNotFoundError,
    ReadToolError,
    read_file,
    read_tool,
)


class TestReadFile:
    """Tests for read_file function"""

    def test_read_simple_file(self, tmp_path: Path) -> None:
        """Test reading a simple text file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")

        result = read_file(str(test_file))

        assert "1→line 1" in result
        assert "2→line 2" in result
        assert "3→line 3" in result

    def test_read_with_offset(self, tmp_path: Path) -> None:
        """Test reading with offset"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line 1\nline 2\nline 3\nline 4\n", encoding="utf-8")

        result = read_file(str(test_file), offset=2)

        assert "1→" not in result
        assert "2→" not in result
        assert "3→line 3" in result
        assert "4→line 4" in result

    def test_read_with_limit(self, tmp_path: Path) -> None:
        """Test reading with limit"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line 1\nline 2\nline 3\nline 4\n", encoding="utf-8")

        result = read_file(str(test_file), limit=2)

        assert "1→line 1" in result
        assert "2→line 2" in result
        assert "3→" not in result
        assert "Showing lines 1-2 of 4" in result

    def test_read_with_offset_and_limit(self, tmp_path: Path) -> None:
        """Test reading with both offset and limit"""
        test_file = tmp_path / "test.txt"
        content = "\n".join([f"line {i}" for i in range(1, 11)])
        test_file.write_text(content, encoding="utf-8")

        result = read_file(str(test_file), offset=3, limit=3)

        assert "4→line 4" in result
        assert "5→line 5" in result
        assert "6→line 6" in result
        assert "3→" not in result
        assert "7→" not in result

    def test_read_nonexistent_file(self, tmp_path: Path) -> None:
        """Test reading a file that doesn't exist"""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError) as exc_info:
            read_file(str(nonexistent))

        assert "File not found" in str(exc_info.value)

    def test_read_binary_file(self, tmp_path: Path) -> None:
        """Test that binary files are rejected"""
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03binary content")

        with pytest.raises(BinaryFileError) as exc_info:
            read_file(str(binary_file))

        assert "Binary file" in str(exc_info.value)

    def test_read_utf8_with_bom(self, tmp_path: Path) -> None:
        """Test that UTF-8 BOM is stripped"""
        test_file = tmp_path / "bom.txt"
        # Write UTF-8 BOM + content
        test_file.write_bytes(b"\xef\xbb\xbfline 1\nline 2\n")

        result = read_file(str(test_file))

        # BOM should be stripped, content should start with line 1
        assert "1→line 1" in result
        assert "\ufeff" not in result

    def test_read_with_encoding_errors(self, tmp_path: Path) -> None:
        """Test that encoding errors are replaced"""
        test_file = tmp_path / "encoding.txt"
        # Write invalid UTF-8 sequence
        test_file.write_bytes(b"valid text\xff\xfeinvalid bytes\n")

        result = read_file(str(test_file))

        # Should not raise, should contain replacement characters
        assert "valid text" in result
        assert "invalid bytes" in result

    def test_read_empty_file(self, tmp_path: Path) -> None:
        """Test reading an empty file"""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        result = read_file(str(test_file))

        assert "Empty" in result or result == ""

    def test_read_relative_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test reading with relative path"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content\n", encoding="utf-8")

        # Change to tmp_path directory
        monkeypatch.chdir(tmp_path)

        result = read_file("test.txt")

        assert "1→content" in result

    def test_read_directory_raises_error(self, tmp_path: Path) -> None:
        """Test that reading a directory raises error"""
        with pytest.raises(ReadToolError) as exc_info:
            read_file(str(tmp_path))

        assert "Not a file" in str(exc_info.value)


class TestReadTool:
    """Tests for read_tool LangChain tool"""

    def test_tool_returns_content(self, tmp_path: Path) -> None:
        """Test that tool returns file content"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world\n", encoding="utf-8")

        result = read_tool.invoke({"file_path": str(test_file)})

        assert "1→hello world" in result

    def test_tool_returns_error_message(self, tmp_path: Path) -> None:
        """Test that tool returns error message instead of raising"""
        nonexistent = tmp_path / "nonexistent.txt"

        result = read_tool.invoke({"file_path": str(nonexistent)})

        assert "Error:" in result
        assert "File not found" in result

    def test_tool_has_correct_name(self) -> None:
        """Test that tool has the expected name"""
        assert read_tool.name == "read_tool"

    def test_tool_has_description(self) -> None:
        """Test that tool has a description"""
        assert read_tool.description is not None
        assert len(read_tool.description) > 0
