"""Interfaces Module

Defines abstract interfaces for swappable components.
"""

from claude_clone.interfaces.checkpoint_manager import (
    CheckpointManager,
    FileCheckpoint,
    FileSnapshot,
)
from claude_clone.interfaces.config_loader import Config, ConfigLoader
from claude_clone.interfaces.grep_backend import GrepBackend, GrepMatch

__all__ = [
    # GrepBackend
    "GrepBackend",
    "GrepMatch",
    # CheckpointManager
    "CheckpointManager",
    "FileCheckpoint",
    "FileSnapshot",
    # ConfigLoader
    "ConfigLoader",
    "Config",
]
