"""ConfigLoader Interface - Configuration Loading Abstraction

MVP: SimpleConfigLoader (single file)
Future: HierarchicalConfigLoader (hierarchical config)

Configuration priority (highest first):
    1. Environment variables (CLAUDE_CLONE_API_KEY, etc.)
    2. Project config (.claude-clone/config.toml)
    3. User config (~/.claude-clone/config.toml)
    4. Defaults
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration"""

    # API settings
    provider: str = Field(
        default="gemini",
        description="LLM provider (gemini, anthropic, openai, ollama)",
    )
    api_key: str | None = Field(
        default=None,
        description="API key (environment variable recommended)",
    )
    model: str = Field(
        default="gemini-3.0-flash-preview",
        description="Model to use",
    )

    # Permission settings
    permission_mode: str = Field(
        default="default",
        description="Permission mode (default, plan, accept_edits, bypass)",
    )
    allow_rules: list[str] = Field(
        default_factory=list,
        description="Allow rules list",
    )
    deny_rules: list[str] = Field(
        default_factory=list,
        description="Deny rules list",
    )

    # Session settings
    history_limit: int = Field(
        default=100,
        description="Maximum conversation history count",
    )
    auto_save: bool = Field(
        default=True,
        description="Auto save enabled",
    )
    retention_days: int = Field(
        default=30,
        description="Session retention period (days)",
    )


class ConfigLoader(ABC):
    """Configuration loader interface

    Implementations:
        - SimpleConfigLoader: Single file loading - MVP
        - HierarchicalConfigLoader: Hierarchical config merging - Future

    Config file locations:
        - User: ~/.claude-clone/config.toml
        - Project: .claude-clone/config.toml

    Environment variable mapping:
        - CLAUDE_CLONE_PROVIDER -> provider
        - CLAUDE_CLONE_API_KEY -> api_key
        - CLAUDE_CLONE_MODEL -> model
        - GOOGLE_API_KEY -> api_key (Gemini fallback)
    """

    @abstractmethod
    def load(self) -> Config:
        """Load configuration

        Merges all config sources (env vars, files, defaults)
        and returns the final Config object.

        Returns:
            Merged configuration object
        """
        pass

    @abstractmethod
    def save_user_config(self, updates: dict[str, Any]) -> None:
        """Save user configuration

        Saves configuration to ~/.claude-clone/config.toml.

        Args:
            updates: Settings to update (partial update)

        Raises:
            PermissionError: When file write permission is denied
        """
        pass

    @abstractmethod
    def save_project_config(self, updates: dict[str, Any]) -> None:
        """Save project configuration

        Saves configuration to .claude-clone/config.toml.

        Args:
            updates: Settings to update (partial update)

        Raises:
            PermissionError: When file write permission is denied
        """
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get single configuration value

        Supports dot notation (e.g., "api.key").

        Args:
            key: Configuration key
            default: Default value (when key not found)

        Returns:
            Configuration value or default
        """
        pass
