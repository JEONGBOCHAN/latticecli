"""Tests for Grep Tool"""

from pathlib import Path

import pytest

from claude_clone.agent.tools.grep import (
    GrepMatch,
    GrepToolError,
    InvalidPatternError,
    PathNotFoundError,
    grep_files,
    grep_tool,
)


class TestGrepFiles:
    """Tests for grep_files function"""

    def test_simple_pattern_match(self, tmp_path: Path) -> None:
        """Test simple pattern matching"""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('world')\n")

        result = grep_files("hello", str(tmp_path))

        assert len(result) == 1
        assert result[0].line_number == 1
        assert "hello" in result[0].content

    def test_regex_pattern(self, tmp_path: Path) -> None:
        """Test regex pattern matching"""
        test_file = tmp_path / "test.py"
        test_file.write_text("foo123\nbar456\nfoo789\n")

        result = grep_files(r"foo\d+", str(tmp_path))

        assert len(result) == 2
        assert result[0].content == "foo123"
        assert result[1].content == "foo789"

    def test_multiple_files(self, tmp_path: Path) -> None:
        """Test searching across multiple files"""
        (tmp_path / "file1.py").write_text("hello world\n")
        (tmp_path / "file2.py").write_text("hello again\n")
        (tmp_path / "file3.py").write_text("goodbye\n")

        result = grep_files("hello", str(tmp_path))

        assert len(result) == 2

    def test_file_type_filter(self, tmp_path: Path) -> None:
        """Test file type filtering"""
        (tmp_path / "test.py").write_text("hello python\n")
        (tmp_path / "test.js").write_text("hello javascript\n")
        (tmp_path / "test.md").write_text("hello markdown\n")

        result = grep_files("hello", str(tmp_path), file_type="py")

        assert len(result) == 1
        assert "test.py" in result[0].file

    def test_context_lines(self, tmp_path: Path) -> None:
        """Test context lines before and after match"""
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nmatch_here\nline4\nline5\n")

        result = grep_files("match_here", str(tmp_path), context_lines=1)

        assert len(result) == 1
        assert result[0].context_before == ["line2"]
        assert result[0].context_after == ["line4"]

    def test_max_results(self, tmp_path: Path) -> None:
        """Test max_results limit"""
        test_file = tmp_path / "test.py"
        test_file.write_text("\n".join(f"match{i}" for i in range(20)))

        result = grep_files("match", str(tmp_path), max_results=5)

        assert len(result) == 5

    def test_invalid_pattern(self, tmp_path: Path) -> None:
        """Test error on invalid regex pattern"""
        (tmp_path / "test.py").write_text("content\n")

        with pytest.raises(InvalidPatternError) as exc_info:
            grep_files("[invalid", str(tmp_path))

        assert "Invalid regex" in str(exc_info.value)

    def test_path_not_found(self, tmp_path: Path) -> None:
        """Test error when path doesn't exist"""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(PathNotFoundError) as exc_info:
            grep_files("pattern", str(nonexistent))

        assert "Path not found" in str(exc_info.value)

    def test_search_single_file(self, tmp_path: Path) -> None:
        """Test searching a single file"""
        test_file = tmp_path / "test.py"
        test_file.write_text("hello\nworld\n")

        result = grep_files("hello", str(test_file))

        assert len(result) == 1

    def test_no_matches(self, tmp_path: Path) -> None:
        """Test when no matches found"""
        (tmp_path / "test.py").write_text("hello world\n")

        result = grep_files("goodbye", str(tmp_path))

        assert result == []

    def test_skip_binary_files(self, tmp_path: Path) -> None:
        """Test that binary files are skipped"""
        (tmp_path / "test.py").write_text("hello text\n")
        (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02hello\x03\x04")

        result = grep_files("hello", str(tmp_path))

        assert len(result) == 1
        assert "test.py" in result[0].file

    def test_skip_hidden_directories(self, tmp_path: Path) -> None:
        """Test that hidden directories are skipped"""
        (tmp_path / "visible.py").write_text("hello visible\n")
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "hidden.py").write_text("hello hidden\n")

        result = grep_files("hello", str(tmp_path))

        assert len(result) == 1
        assert "visible.py" in result[0].file

    def test_relative_file_paths(self, tmp_path: Path) -> None:
        """Test that file paths in results are relative"""
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "test.py").write_text("hello\n")

        result = grep_files("hello", str(tmp_path))

        assert len(result) == 1
        assert not Path(result[0].file).is_absolute()

    def test_line_numbers_are_one_based(self, tmp_path: Path) -> None:
        """Test that line numbers start at 1"""
        test_file = tmp_path / "test.py"
        test_file.write_text("FINDME_first\nno find here\nFINDME_third\n")

        result = grep_files("FINDME", str(tmp_path))

        assert len(result) == 2
        assert result[0].line_number == 1
        assert result[1].line_number == 3


class TestGrepTool:
    """Tests for grep_tool LangChain tool"""

    def test_tool_returns_matches(self, tmp_path: Path) -> None:
        """Test that tool returns formatted matches"""
        (tmp_path / "test.py").write_text("hello world\ngoodbye world\n")

        result = grep_tool.invoke({"pattern": "hello", "path": str(tmp_path)})

        assert "Found 1 match" in result
        assert "test.py" in result
        assert "hello" in result

    def test_tool_returns_no_matches_message(self, tmp_path: Path) -> None:
        """Test message when no matches found"""
        (tmp_path / "test.py").write_text("hello world\n")

        result = grep_tool.invoke({"pattern": "goodbye", "path": str(tmp_path)})

        assert "No matches found" in result

    def test_tool_returns_error_on_invalid_pattern(self, tmp_path: Path) -> None:
        """Test that invalid pattern returns error message"""
        (tmp_path / "test.py").write_text("content\n")

        result = grep_tool.invoke({"pattern": "[invalid", "path": str(tmp_path)})

        assert "Error:" in result
        assert "Invalid regex" in result

    def test_tool_has_correct_name(self) -> None:
        """Test that tool has the expected name"""
        assert grep_tool.name == "grep_tool"

    def test_tool_has_description(self) -> None:
        """Test that tool has a description"""
        assert grep_tool.description is not None
        assert len(grep_tool.description) > 0

    def test_tool_with_file_type(self, tmp_path: Path) -> None:
        """Test file type parameter"""
        (tmp_path / "test.py").write_text("hello python\n")
        (tmp_path / "test.js").write_text("hello javascript\n")

        result = grep_tool.invoke({
            "pattern": "hello",
            "path": str(tmp_path),
            "file_type": "py",
        })

        assert "python" in result
        assert "javascript" not in result

    def test_tool_with_context_lines(self, tmp_path: Path) -> None:
        """Test context lines parameter"""
        (tmp_path / "test.py").write_text("before\nmatch\nafter\n")

        result = grep_tool.invoke({
            "pattern": "match",
            "path": str(tmp_path),
            "context_lines": 1,
        })

        assert "before" in result
        assert "after" in result


class TestGrepMatch:
    """Tests for GrepMatch dataclass"""

    def test_grep_match_creation(self) -> None:
        """Test creating a GrepMatch"""
        match = GrepMatch(
            file="test.py",
            line_number=10,
            content="hello world",
        )

        assert match.file == "test.py"
        assert match.line_number == 10
        assert match.content == "hello world"
        assert match.context_before == []
        assert match.context_after == []

    def test_grep_match_with_context(self) -> None:
        """Test GrepMatch with context lines"""
        match = GrepMatch(
            file="test.py",
            line_number=10,
            content="match line",
            context_before=["line 9"],
            context_after=["line 11"],
        )

        assert match.context_before == ["line 9"]
        assert match.context_after == ["line 11"]
