"""Tests for Glob Tool"""

from pathlib import Path

import pytest

from claude_clone.agent.tools.glob import (
    DirectoryNotFoundError,
    GlobToolError,
    glob_files,
    glob_tool,
)


class TestGlobFiles:
    """Tests for glob_files function"""

    def test_find_python_files(self, tmp_path: Path) -> None:
        """Test finding Python files"""
        # Create test files
        (tmp_path / "main.py").write_text("print('main')")
        (tmp_path / "utils.py").write_text("print('utils')")
        (tmp_path / "readme.md").write_text("# Readme")

        result = glob_files("*.py", str(tmp_path))

        assert len(result) == 2
        assert "main.py" in result
        assert "utils.py" in result
        assert "readme.md" not in result

    def test_recursive_glob(self, tmp_path: Path) -> None:
        """Test recursive glob pattern"""
        # Create nested structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("app")
        (tmp_path / "src" / "utils").mkdir()
        (tmp_path / "src" / "utils" / "helper.py").write_text("helper")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_app.py").write_text("test")

        result = glob_files("**/*.py", str(tmp_path))

        assert len(result) == 3
        assert any("app.py" in p for p in result)
        assert any("helper.py" in p for p in result)
        assert any("test_app.py" in p for p in result)

    def test_no_matches(self, tmp_path: Path) -> None:
        """Test when no files match pattern"""
        (tmp_path / "readme.md").write_text("# Readme")

        result = glob_files("*.py", str(tmp_path))

        assert result == []

    def test_directory_not_found(self, tmp_path: Path) -> None:
        """Test error when directory doesn't exist"""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(DirectoryNotFoundError) as exc_info:
            glob_files("*.py", str(nonexistent))

        assert "Directory not found" in str(exc_info.value)

    def test_not_a_directory(self, tmp_path: Path) -> None:
        """Test error when path is a file, not directory"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with pytest.raises(GlobToolError) as exc_info:
            glob_files("*.py", str(test_file))

        assert "Not a directory" in str(exc_info.value)

    def test_max_results(self, tmp_path: Path) -> None:
        """Test max_results limit"""
        # Create many files
        for i in range(10):
            (tmp_path / f"file{i}.py").write_text(f"content {i}")

        result = glob_files("*.py", str(tmp_path), max_results=3)

        assert len(result) == 3

    def test_relative_path_result(self, tmp_path: Path) -> None:
        """Test that results are relative paths"""
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "test.py").write_text("test")

        result = glob_files("**/*.py", str(tmp_path))

        # Should be relative path, not absolute
        assert len(result) == 1
        assert not Path(result[0]).is_absolute()
        assert "subdir" in result[0]

    def test_sorted_results(self, tmp_path: Path) -> None:
        """Test that results are sorted"""
        (tmp_path / "z_last.py").write_text("z")
        (tmp_path / "a_first.py").write_text("a")
        (tmp_path / "m_middle.py").write_text("m")

        result = glob_files("*.py", str(tmp_path))

        assert result == sorted(result)

    def test_only_files_not_directories(self, tmp_path: Path) -> None:
        """Test that only files are returned, not directories"""
        (tmp_path / "test.py").write_text("test")
        (tmp_path / "package.py").mkdir()  # Directory with .py name

        result = glob_files("*.py", str(tmp_path))

        assert len(result) == 1
        assert "test.py" in result


class TestGlobTool:
    """Tests for glob_tool LangChain tool"""

    def test_tool_returns_matches(self, tmp_path: Path) -> None:
        """Test that tool returns formatted matches"""
        (tmp_path / "test.py").write_text("test")
        (tmp_path / "main.py").write_text("main")

        result = glob_tool.invoke({"pattern": "*.py", "path": str(tmp_path)})

        assert "Found 2 file(s)" in result
        assert "test.py" in result
        assert "main.py" in result

    def test_tool_returns_no_matches_message(self, tmp_path: Path) -> None:
        """Test message when no files match"""
        (tmp_path / "readme.md").write_text("readme")

        result = glob_tool.invoke({"pattern": "*.py", "path": str(tmp_path)})

        assert "No files found" in result

    def test_tool_returns_error_message(self, tmp_path: Path) -> None:
        """Test that tool returns error message instead of raising"""
        nonexistent = tmp_path / "nonexistent"

        result = glob_tool.invoke({"pattern": "*.py", "path": str(nonexistent)})

        assert "Error:" in result
        assert "Directory not found" in result

    def test_tool_has_correct_name(self) -> None:
        """Test that tool has the expected name"""
        assert glob_tool.name == "glob_tool"

    def test_tool_has_description(self) -> None:
        """Test that tool has a description"""
        assert glob_tool.description is not None
        assert len(glob_tool.description) > 0

    def test_tool_default_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that default path is current directory"""
        (tmp_path / "test.py").write_text("test")
        monkeypatch.chdir(tmp_path)

        result = glob_tool.invoke({"pattern": "*.py"})

        assert "test.py" in result
