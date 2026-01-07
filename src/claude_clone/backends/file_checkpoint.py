"""FileCheckpointManager - File-based checkpoint implementation

Stores file snapshots as JSON for rollback purposes.
MVP implementation using simple file storage.

Usage:
    from claude_clone.backends.file_checkpoint import FileCheckpointManager

    manager = FileCheckpointManager(storage_dir="~/.claude-clone/checkpoints")
    manager.track_file("src/main.py")
    checkpoint = manager.create("Before refactoring")
    # ... make changes ...
    manager.restore(checkpoint.id)  # Rollback
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from claude_clone.interfaces import CheckpointManager, FileCheckpoint, FileSnapshot


class CheckpointError(Exception):
    """Base error for checkpoint operations"""

    pass


class CheckpointNotFoundError(CheckpointError):
    """Checkpoint not found"""

    pass


class FileCheckpointManager(CheckpointManager):
    """File-based checkpoint manager

    Stores checkpoints as JSON files in a storage directory.
    Each checkpoint contains snapshots of tracked files.

    Attributes:
        storage_dir: Directory to store checkpoint files
        tracked_files: Currently tracked file paths and their original content
        turn: Current conversation turn number
    """

    def __init__(
        self,
        storage_dir: str | Path | None = None,
        turn: int = 0,
    ):
        """Initialize FileCheckpointManager

        Args:
            storage_dir: Directory to store checkpoints.
                         Default: ~/.claude-clone/checkpoints
            turn: Initial conversation turn number
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".claude-clone" / "checkpoints"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._tracked_files: dict[str, FileSnapshot | None] = {}
        self._turn = turn

    @property
    def turn(self) -> int:
        """Current conversation turn number"""
        return self._turn

    def increment_turn(self) -> int:
        """Increment turn number and return new value"""
        self._turn += 1
        return self._turn

    def track_file(self, file_path: str) -> None:
        """Start tracking a file for potential rollback

        Saves the current content of the file before modification.

        Args:
            file_path: Path to the file to track
        """
        # Normalize path
        path = Path(file_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        path_str = str(path)

        # Skip if already tracked in this turn
        if path_str in self._tracked_files:
            return

        # Save current state (or None if file doesn't exist)
        if path.exists() and path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
                mtime = path.stat().st_mtime
                self._tracked_files[path_str] = FileSnapshot(
                    path=path_str,
                    content=content,
                    mtime=mtime,
                )
            except (OSError, UnicodeDecodeError):
                # Can't read file, mark as new
                self._tracked_files[path_str] = None
        else:
            # File doesn't exist, mark as new
            self._tracked_files[path_str] = None

    def create(self, message: str) -> FileCheckpoint:
        """Create a checkpoint from currently tracked files

        Args:
            message: Description of the checkpoint

        Returns:
            Created FileCheckpoint
        """
        checkpoint_id = str(uuid.uuid4())
        timestamp = datetime.now()

        # Collect snapshots from tracked files
        snapshots = [
            snapshot
            for snapshot in self._tracked_files.values()
            if snapshot is not None
        ]

        checkpoint = FileCheckpoint(
            id=checkpoint_id,
            turn=self._turn,
            timestamp=timestamp,
            message=message,
            snapshots=snapshots,
        )

        # Save to file
        self._save_checkpoint(checkpoint)

        # Clear tracked files for next turn
        self._tracked_files.clear()

        return checkpoint

    def restore(self, checkpoint_id: str) -> list[str]:
        """Restore files from a checkpoint

        Args:
            checkpoint_id: ID of the checkpoint to restore

        Returns:
            List of restored file paths

        Raises:
            CheckpointNotFoundError: If checkpoint doesn't exist
        """
        checkpoint = self._load_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise CheckpointNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        restored_paths: list[str] = []

        for snapshot in checkpoint.snapshots:
            try:
                path = Path(snapshot.path)
                # Create parent directories if needed
                path.parent.mkdir(parents=True, exist_ok=True)
                # Restore content
                path.write_text(snapshot.content, encoding="utf-8")
                restored_paths.append(snapshot.path)
            except OSError:
                # Skip files that can't be restored
                continue

        return restored_paths

    def list_checkpoints(self, limit: int = 10) -> list[FileCheckpoint]:
        """List recent checkpoints

        Args:
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoints, newest first
        """
        checkpoints: list[FileCheckpoint] = []

        # Load all checkpoint files
        for checkpoint_file in self.storage_dir.glob("*.json"):
            try:
                checkpoint = self._load_checkpoint_from_file(checkpoint_file)
                if checkpoint:
                    checkpoints.append(checkpoint)
            except Exception:
                # Skip invalid files
                continue

        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda c: c.timestamp, reverse=True)

        return checkpoints[:limit]

    def clear_old(self, keep_last: int = 50) -> int:
        """Remove old checkpoints, keeping only the most recent

        Args:
            keep_last: Number of recent checkpoints to keep

        Returns:
            Number of deleted checkpoints
        """
        checkpoints = self.list_checkpoints(limit=10000)  # Get all

        if len(checkpoints) <= keep_last:
            return 0

        # Delete old ones
        to_delete = checkpoints[keep_last:]
        deleted_count = 0

        for checkpoint in to_delete:
            checkpoint_file = self.storage_dir / f"{checkpoint.id}.json"
            try:
                checkpoint_file.unlink()
                deleted_count += 1
            except OSError:
                continue

        return deleted_count

    def clear_tracked(self) -> None:
        """Clear currently tracked files without creating checkpoint"""
        self._tracked_files.clear()

    def get_tracked_files(self) -> list[str]:
        """Get list of currently tracked file paths"""
        return list(self._tracked_files.keys())

    def _save_checkpoint(self, checkpoint: FileCheckpoint) -> None:
        """Save checkpoint to file"""
        checkpoint_file = self.storage_dir / f"{checkpoint.id}.json"
        data = checkpoint.model_dump(mode="json")
        checkpoint_file.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )

    def _load_checkpoint(self, checkpoint_id: str) -> FileCheckpoint | None:
        """Load checkpoint by ID"""
        checkpoint_file = self.storage_dir / f"{checkpoint_id}.json"
        return self._load_checkpoint_from_file(checkpoint_file)

    def _load_checkpoint_from_file(self, file_path: Path) -> FileCheckpoint | None:
        """Load checkpoint from file"""
        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return FileCheckpoint.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return None
