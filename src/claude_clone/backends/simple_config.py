"""SimpleConfigLoader - MVP Configuration Loader

Loads configuration from environment variables and TOML files.
Priority (highest first): env > project > user > defaults
"""

import os
import tomllib
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from claude_clone.interfaces import Config, ConfigLoader


class ConfigurationError(Exception):
    """Configuration related errors"""

    pass


class SimpleConfigLoader(ConfigLoader):
    """Simple configuration loader implementation

    Loads configuration with the following priority:
        1. Environment variables
        2. Project config (.claude-clone/config.toml)
        3. User config (~/.claude-clone/config.toml)
        4. Defaults (from Config model)

    Environment variable mapping:
        - CLAUDE_CLONE_PROVIDER -> provider
        - CLAUDE_CLONE_API_KEY -> api_key
        - CLAUDE_CLONE_MODEL -> model
        - GOOGLE_API_KEY -> api_key (Gemini fallback)

    .env file loading:
        - Only loads from project_root/.env
        - User home .env is NOT loaded (use environment variables instead)
    """

    # Path constants
    CONFIG_DIR_NAME: str = ".claude-clone"
    CONFIG_FILE_NAME: str = "config.toml"

    # Environment variable to Config field mapping
    ENV_MAPPING: dict[str, str] = {
        "CLAUDE_CLONE_PROVIDER": "provider",
        "CLAUDE_CLONE_API_KEY": "api_key",
        "CLAUDE_CLONE_MODEL": "model",
    }

    # Fallback environment variables
    API_KEY_FALLBACKS: list[str] = [
        "GOOGLE_API_KEY",  # Gemini
        "ANTHROPIC_API_KEY",  # Claude
        "OPENAI_API_KEY",  # OpenAI
    ]

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize the config loader

        Args:
            project_root: Project root directory. If None, uses current directory.
        """
        self._project_root = project_root or Path.cwd()
        self._config: Config | None = None

        # Load .env file if exists
        env_file = self._project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    @property
    def user_config_path(self) -> Path:
        """User config file path: ~/.claude-clone/config.toml"""
        return Path.home() / self.CONFIG_DIR_NAME / self.CONFIG_FILE_NAME

    @property
    def project_config_path(self) -> Path:
        """Project config file path: .claude-clone/config.toml"""
        return self._project_root / self.CONFIG_DIR_NAME / self.CONFIG_FILE_NAME

    def load(self) -> Config:
        """Load configuration from all sources

        Returns:
            Merged configuration object

        Raises:
            ConfigurationError: When API key is missing
        """
        # Start with defaults
        config_dict: dict[str, Any] = {}

        # Load user config (lowest priority file)
        user_config = self._load_toml(self.user_config_path)
        config_dict.update(user_config)

        # Load project config (higher priority)
        project_config = self._load_toml(self.project_config_path)
        config_dict.update(project_config)

        # Load environment variables (highest priority)
        env_config = self._load_env()
        config_dict.update(env_config)

        # Create Config object (applies defaults for missing fields)
        self._config = Config(**config_dict)

        # Validate API key
        self._validate_api_key()

        return self._config

    def save_user_config(self, updates: dict[str, Any]) -> None:
        """Save user configuration

        Args:
            updates: Settings to update (partial update)

        Raises:
            PermissionError: When file write permission is denied
        """
        self._save_toml(self.user_config_path, updates)

    def save_project_config(self, updates: dict[str, Any]) -> None:
        """Save project configuration

        Args:
            updates: Settings to update (partial update)

        Raises:
            PermissionError: When file write permission is denied
        """
        self._save_toml(self.project_config_path, updates)

    def get(self, key: str, default: Any = None) -> Any:
        """Get single configuration value

        Supports dot notation (e.g., "api_key", "permission_mode").

        Args:
            key: Configuration key
            default: Default value (when key not found)

        Returns:
            Configuration value or default
        """
        if self._config is None:
            self.load()

        assert self._config is not None

        # Handle dot notation (for future nested config)
        parts = key.split(".")

        # For now, Config is flat, so just get the first part
        if len(parts) == 1:
            return getattr(self._config, key, default)

        # Future: nested config support
        # For now, treat as flat
        return getattr(self._config, parts[0], default)

    def _load_toml(self, path: Path) -> dict[str, Any]:
        """Load TOML file if exists

        Args:
            path: Path to TOML file

        Returns:
            Parsed TOML as dict, or empty dict if file doesn't exist
        """
        if not path.exists():
            return {}

        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ConfigurationError(f"Invalid TOML in {path}: {e}") from e

    def _save_toml(self, path: Path, updates: dict[str, Any]) -> None:
        """Save updates to TOML file

        Args:
            path: Path to TOML file
            updates: Settings to update

        Raises:
            PermissionError: When file write permission is denied
        """
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config
        existing = self._load_toml(path)

        # Merge updates
        existing.update(updates)

        # Write back
        # Note: tomllib is read-only, we need to write manually
        lines = []
        for key, value in existing.items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, bool):
                lines.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, (int, float)):
                lines.append(f"{key} = {value}")
            elif isinstance(value, list):
                items = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                lines.append(f"{key} = [{items}]")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def _load_env(self) -> dict[str, Any]:
        """Load configuration from environment variables

        Returns:
            Dict of config values from environment
        """
        config: dict[str, Any] = {}

        # Load mapped environment variables
        for env_var, config_key in self.ENV_MAPPING.items():
            value = os.environ.get(env_var)
            if value is not None:
                config[config_key] = value

        # Load API key fallbacks if not already set
        if "api_key" not in config:
            for fallback_var in self.API_KEY_FALLBACKS:
                value = os.environ.get(fallback_var)
                if value is not None:
                    config["api_key"] = value
                    break

        return config

    def _validate_api_key(self) -> None:
        """Validate that API key is present

        Raises:
            ConfigurationError: When API key is missing
        """
        if self._config is None or not self._config.api_key:
            raise ConfigurationError(
                "API key is required.\n\n"
                "Please set one of the following:\n"
                "  1. Environment variable: GOOGLE_API_KEY (for Gemini)\n"
                "  2. Environment variable: CLAUDE_CLONE_API_KEY\n"
                "  3. .env file: GOOGLE_API_KEY=your-key-here\n"
                "  4. Config file: ~/.claude-clone/config.toml\n"
                "     api_key = \"your-key-here\"\n"
            )
