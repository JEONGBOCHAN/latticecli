"""CheckpointManager Interface - File Rollback Abstraction

MVP: FileCheckpointManager (file snapshots)
Future: GitCheckpointManager (Git stash)

Note: This is separate from LangGraph's SqliteSaver (conversation state).
      It manages file change history for rollback purposes.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel


class FileSnapshot(BaseModel):
    """File snapshot"""

    path: str
    """File path (absolute)"""

    content: str
    """File content (UTF-8)"""

    mtime: float
    """Modification time (timestamp)"""


class FileCheckpoint(BaseModel):
    """Checkpoint (collection of file snapshots)"""

    id: str
    """Checkpoint ID (UUID)"""

    turn: int
    """Conversation turn number"""

    timestamp: datetime
    """Creation time"""

    message: str
    """Checkpoint description (e.g., "Edit main.py")"""

    snapshots: list[FileSnapshot]
    """List of file snapshots"""


class CheckpointManager(ABC):
    """File checkpoint manager interface

    Implementations:
        - FileCheckpointManager: File snapshot approach (JSON storage) - MVP
        - GitCheckpointManager: Git stash utilization - Future

    Usage flow:
        1. Call track_file() before file modification in Edit/Write tools
        2. Call create() after tool execution to create checkpoint
        3. Call restore() via /rewind or Esc+Esc
    """

    @abstractmethod
    def create(self, message: str) -> FileCheckpoint:
        """Create a checkpoint

        Saves snapshots of all currently tracked files.

        Args:
            message: Checkpoint description (e.g., "Before editing main.py")

        Returns:
            Created checkpoint
        """
        pass

    @abstractmethod
    def track_file(self, file_path: str) -> None:
        """Start tracking file changes

        Call before modifying a file to save the original content.
        Recommended to be called automatically by Edit/Write tools.

        Args:
            file_path: Path to the file to track

        Note:
            Already tracked files are ignored.
            Non-existent files are recorded as "new file".
        """
        pass

    @abstractmethod
    def restore(self, checkpoint_id: str) -> list[str]:
        """Restore files from checkpoint

        Args:
            checkpoint_id: ID of checkpoint to restore

        Returns:
            List of restored file paths

        Raises:
            KeyError: When checkpoint is not found
        """
        pass

    @abstractmethod
    def list_checkpoints(self, limit: int = 10) -> list[FileCheckpoint]:
        """List checkpoints

        Args:
            limit: Maximum number to return (newest first)

        Returns:
            List of checkpoints (sorted by newest)
        """
        pass

    @abstractmethod
    def clear_old(self, keep_last: int = 50) -> int:
        """Clean up old checkpoints

        Args:
            keep_last: Number of recent checkpoints to keep

        Returns:
            Number of deleted checkpoints
        """
        pass
