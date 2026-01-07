"""Tests for SimpleConfigLoader"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_clone.backends import ConfigurationError, SimpleConfigLoader
from claude_clone.interfaces import Config


class TestSimpleConfigLoader:
    """SimpleConfigLoader tests"""

    def test_load_with_env_api_key(self, tmp_path: Path) -> None:
        """Test loading config with API key from environment"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-api-key"}, clear=False):
            loader = SimpleConfigLoader(project_root=tmp_path)
            config = loader.load()

            assert config.api_key == "test-api-key"
            assert config.provider == "gemini"  # default
            assert config.model == "gemini-3-flash-preview"  # default

    def test_load_without_api_key_raises_error(self, tmp_path: Path) -> None:
        """Test that missing API key raises ConfigurationError"""
        # Clear all API key environment variables
        env_clear = {
            "GOOGLE_API_KEY": None,
            "ANTHROPIC_API_KEY": None,
            "OPENAI_API_KEY": None,
            "CLAUDE_CLONE_API_KEY": None,
        }

        with patch.dict(os.environ, {k: v for k, v in env_clear.items() if v is not None}):
            # Remove the keys
            for key in env_clear:
                os.environ.pop(key, None)

            loader = SimpleConfigLoader(project_root=tmp_path)

            with pytest.raises(ConfigurationError) as exc_info:
                loader.load()

            assert "API key is required" in str(exc_info.value)

    def test_env_override_priority(self, tmp_path: Path) -> None:
        """Test that environment variables override config files"""
        # Create user config
        user_config_dir = Path.home() / ".claude-clone"
        user_config_dir.mkdir(parents=True, exist_ok=True)

        with patch.dict(
            os.environ,
            {
                "GOOGLE_API_KEY": "env-api-key",
                "CLAUDE_CLONE_MODEL": "custom-model",
            },
            clear=False,
        ):
            loader = SimpleConfigLoader(project_root=tmp_path)
            config = loader.load()

            assert config.api_key == "env-api-key"
            assert config.model == "custom-model"

    def test_get_method(self, tmp_path: Path) -> None:
        """Test get() method for single value retrieval"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=False):
            loader = SimpleConfigLoader(project_root=tmp_path)

            # get() should trigger load() if not already loaded
            assert loader.get("api_key") == "test-key"
            assert loader.get("provider") == "gemini"
            assert loader.get("nonexistent", "default") == "default"

    def test_load_from_toml_file(self, tmp_path: Path) -> None:
        """Test loading config from TOML file"""
        # Create project config
        config_dir = tmp_path / ".claude-clone"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text(
            'api_key = "toml-api-key"\n'
            'model = "custom-model"\n'
            'provider = "gemini"\n'
        )

        loader = SimpleConfigLoader(project_root=tmp_path)
        config = loader.load()

        assert config.api_key == "toml-api-key"
        assert config.model == "custom-model"

    def test_save_project_config(self, tmp_path: Path) -> None:
        """Test saving project config"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=False):
            loader = SimpleConfigLoader(project_root=tmp_path)
            loader.load()

            # Save config
            loader.save_project_config({"model": "new-model"})

            # Verify file was created
            config_file = tmp_path / ".claude-clone" / "config.toml"
            assert config_file.exists()

            content = config_file.read_text()
            assert 'model = "new-model"' in content

    def test_dotenv_loading(self, tmp_path: Path) -> None:
        """Test that .env file is loaded"""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("GOOGLE_API_KEY=dotenv-api-key\n")

        loader = SimpleConfigLoader(project_root=tmp_path)
        config = loader.load()

        assert config.api_key == "dotenv-api-key"

    def test_api_key_fallback_order(self, tmp_path: Path) -> None:
        """Test API key fallback order"""
        # Only ANTHROPIC_API_KEY set
        with patch.dict(
            os.environ,
            {"ANTHROPIC_API_KEY": "anthropic-key"},
            clear=False,
        ):
            # Remove other keys
            os.environ.pop("GOOGLE_API_KEY", None)
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("CLAUDE_CLONE_API_KEY", None)

            loader = SimpleConfigLoader(project_root=tmp_path)
            config = loader.load()

            assert config.api_key == "anthropic-key"

    def test_project_overrides_user_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that project config overrides user config"""
        # Clear environment variables to isolate test
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("CLAUDE_CLONE_API_KEY", raising=False)

        # Create a fake user home directory
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create user config with model = "user-model"
        user_config_dir = fake_home / ".claude-clone"
        user_config_dir.mkdir(parents=True)
        user_config_file = user_config_dir / "config.toml"
        user_config_file.write_text(
            'api_key = "user-api-key"\n'
            'model = "user-model"\n'
            'provider = "gemini"\n'
        )

        # Create project config with model = "project-model"
        project_root = tmp_path / "project"
        project_root.mkdir()
        project_config_dir = project_root / ".claude-clone"
        project_config_dir.mkdir(parents=True)
        project_config_file = project_config_dir / "config.toml"
        project_config_file.write_text(
            'model = "project-model"\n'
        )

        loader = SimpleConfigLoader(project_root=project_root)
        config = loader.load()

        # Project config should override user config
        assert config.model == "project-model"
        # User config should still provide api_key (not overridden by project)
        assert config.api_key == "user-api-key"

    def test_env_overrides_all_configs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override all config files"""
        # Create a fake user home directory
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create user config
        user_config_dir = fake_home / ".claude-clone"
        user_config_dir.mkdir(parents=True)
        user_config_file = user_config_dir / "config.toml"
        user_config_file.write_text(
            'api_key = "user-api-key"\n'
            'model = "user-model"\n'
        )

        # Create project config
        project_root = tmp_path / "project"
        project_root.mkdir()
        project_config_dir = project_root / ".claude-clone"
        project_config_dir.mkdir(parents=True)
        project_config_file = project_config_dir / "config.toml"
        project_config_file.write_text(
            'model = "project-model"\n'
        )

        # Set environment variable
        with patch.dict(
            os.environ,
            {
                "GOOGLE_API_KEY": "env-api-key",
                "CLAUDE_CLONE_MODEL": "env-model",
            },
            clear=False,
        ):
            loader = SimpleConfigLoader(project_root=project_root)
            config = loader.load()

            # Environment should override everything
            assert config.api_key == "env-api-key"
            assert config.model == "env-model"

    def test_invalid_toml_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid TOML file raises ConfigurationError"""
        # Create invalid TOML file
        config_dir = tmp_path / ".claude-clone"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text("invalid toml content = = =\n")

        loader = SimpleConfigLoader(project_root=tmp_path)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load()

        assert "Invalid TOML" in str(exc_info.value)
