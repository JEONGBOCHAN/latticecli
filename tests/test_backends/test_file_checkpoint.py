"""Tests for FileCheckpointManager"""

from pathlib import Path

import pytest

from claude_clone.backends.file_checkpoint import (
    CheckpointNotFoundError,
    FileCheckpointManager,
)
from claude_clone.interfaces import FileCheckpoint, FileSnapshot


class TestFileCheckpointManager:
    """Tests for FileCheckpointManager"""

    def test_init_creates_storage_dir(self, tmp_path: Path) -> None:
        """Test that init creates storage directory"""
        storage_dir = tmp_path / "checkpoints"
        assert not storage_dir.exists()

        manager = FileCheckpointManager(storage_dir=storage_dir)

        assert storage_dir.exists()
        assert manager.storage_dir == storage_dir

    def test_track_file_saves_content(self, tmp_path: Path) -> None:
        """Test tracking a file saves its content"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("original content", encoding="utf-8")

        manager.track_file(str(test_file))

        tracked = manager.get_tracked_files()
        assert len(tracked) == 1
        assert str(test_file.resolve()) in tracked

    def test_track_nonexistent_file(self, tmp_path: Path) -> None:
        """Test tracking a file that doesn't exist"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        nonexistent = tmp_path / "nonexistent.py"

        manager.track_file(str(nonexistent))

        tracked = manager.get_tracked_files()
        assert len(tracked) == 1

    def test_track_file_only_once(self, tmp_path: Path) -> None:
        """Test that same file is only tracked once"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        manager.track_file(str(test_file))
        manager.track_file(str(test_file))

        tracked = manager.get_tracked_files()
        assert len(tracked) == 1

    def test_create_checkpoint(self, tmp_path: Path) -> None:
        """Test creating a checkpoint"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("original", encoding="utf-8")

        manager.track_file(str(test_file))
        checkpoint = manager.create("Test checkpoint")

        assert checkpoint.id is not None
        assert checkpoint.message == "Test checkpoint"
        assert len(checkpoint.snapshots) == 1
        assert checkpoint.snapshots[0].content == "original"

    def test_create_clears_tracked_files(self, tmp_path: Path) -> None:
        """Test that create clears tracked files"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        manager.track_file(str(test_file))
        manager.create("Checkpoint")

        assert manager.get_tracked_files() == []

    def test_create_saves_checkpoint_file(self, tmp_path: Path) -> None:
        """Test that checkpoint is saved to file"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        manager.track_file(str(test_file))
        checkpoint = manager.create("Saved checkpoint")

        checkpoint_file = storage_dir / f"{checkpoint.id}.json"
        assert checkpoint_file.exists()

    def test_restore_checkpoint(self, tmp_path: Path) -> None:
        """Test restoring files from checkpoint"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("original", encoding="utf-8")

        manager.track_file(str(test_file))
        checkpoint = manager.create("Before change")

        # Modify the file
        test_file.write_text("modified", encoding="utf-8")
        assert test_file.read_text() == "modified"

        # Restore
        restored = manager.restore(checkpoint.id)

        assert len(restored) == 1
        assert test_file.read_text() == "original"

    def test_restore_nonexistent_checkpoint(self, tmp_path: Path) -> None:
        """Test restoring from nonexistent checkpoint"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        with pytest.raises(CheckpointNotFoundError):
            manager.restore("nonexistent-id")

    def test_list_checkpoints(self, tmp_path: Path) -> None:
        """Test listing checkpoints"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        # Create multiple checkpoints
        for i in range(3):
            manager.track_file(str(test_file))
            manager.create(f"Checkpoint {i}")

        checkpoints = manager.list_checkpoints()

        assert len(checkpoints) == 3
        # Verify newest first
        assert checkpoints[0].message == "Checkpoint 2"

    def test_list_checkpoints_limit(self, tmp_path: Path) -> None:
        """Test list_checkpoints with limit"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        for i in range(5):
            manager.track_file(str(test_file))
            manager.create(f"Checkpoint {i}")

        checkpoints = manager.list_checkpoints(limit=2)

        assert len(checkpoints) == 2

    def test_clear_old_checkpoints(self, tmp_path: Path) -> None:
        """Test clearing old checkpoints"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        for i in range(5):
            manager.track_file(str(test_file))
            manager.create(f"Checkpoint {i}")

        deleted = manager.clear_old(keep_last=2)

        assert deleted == 3
        assert len(manager.list_checkpoints()) == 2

    def test_clear_old_when_under_limit(self, tmp_path: Path) -> None:
        """Test clear_old when checkpoints are under limit"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        manager.track_file(str(test_file))
        manager.create("Only checkpoint")

        deleted = manager.clear_old(keep_last=10)

        assert deleted == 0

    def test_increment_turn(self, tmp_path: Path) -> None:
        """Test turn number incrementation"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir, turn=0)

        assert manager.turn == 0

        new_turn = manager.increment_turn()
        assert new_turn == 1
        assert manager.turn == 1

    def test_checkpoint_stores_turn(self, tmp_path: Path) -> None:
        """Test that checkpoint stores current turn"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir, turn=5)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        manager.track_file(str(test_file))
        checkpoint = manager.create("Checkpoint")

        assert checkpoint.turn == 5

    def test_clear_tracked(self, tmp_path: Path) -> None:
        """Test clearing tracked files without creating checkpoint"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        test_file = tmp_path / "test.py"
        test_file.write_text("content", encoding="utf-8")

        manager.track_file(str(test_file))
        assert len(manager.get_tracked_files()) == 1

        manager.clear_tracked()
        assert len(manager.get_tracked_files()) == 0

    def test_restore_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that restore creates parent directories if needed"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        nested_dir = tmp_path / "src" / "deep" / "nested"
        nested_dir.mkdir(parents=True)
        test_file = nested_dir / "test.py"
        test_file.write_text("original", encoding="utf-8")

        manager.track_file(str(test_file))
        checkpoint = manager.create("Checkpoint")

        # Delete the entire directory tree
        import shutil
        shutil.rmtree(tmp_path / "src")

        # Restore should recreate directories
        restored = manager.restore(checkpoint.id)

        assert len(restored) == 1
        assert test_file.exists()
        assert test_file.read_text() == "original"

    def test_multiple_files_in_checkpoint(self, tmp_path: Path) -> None:
        """Test checkpoint with multiple files"""
        storage_dir = tmp_path / "checkpoints"
        manager = FileCheckpointManager(storage_dir=storage_dir)

        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("content1", encoding="utf-8")
        file2.write_text("content2", encoding="utf-8")

        manager.track_file(str(file1))
        manager.track_file(str(file2))
        checkpoint = manager.create("Multiple files")

        assert len(checkpoint.snapshots) == 2

        # Modify files
        file1.write_text("modified1", encoding="utf-8")
        file2.write_text("modified2", encoding="utf-8")

        # Restore
        manager.restore(checkpoint.id)

        assert file1.read_text() == "content1"
        assert file2.read_text() == "content2"


class TestFileSnapshot:
    """Tests for FileSnapshot model"""

    def test_snapshot_creation(self) -> None:
        """Test creating a FileSnapshot"""
        snapshot = FileSnapshot(
            path="/path/to/file.py",
            content="print('hello')",
            mtime=1234567890.0,
        )

        assert snapshot.path == "/path/to/file.py"
        assert snapshot.content == "print('hello')"
        assert snapshot.mtime == 1234567890.0


class TestFileCheckpoint:
    """Tests for FileCheckpoint model"""

    def test_checkpoint_creation(self) -> None:
        """Test creating a FileCheckpoint"""
        from datetime import datetime

        checkpoint = FileCheckpoint(
            id="test-id",
            turn=1,
            timestamp=datetime.now(),
            message="Test checkpoint",
            snapshots=[],
        )

        assert checkpoint.id == "test-id"
        assert checkpoint.turn == 1
        assert checkpoint.message == "Test checkpoint"
        assert checkpoint.snapshots == []
