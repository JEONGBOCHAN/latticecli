"""Tests for CLI Application"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from claude_clone.cli.app import app


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner"""
    return CliRunner()


class TestCLIHelp:
    """Tests for CLI help and basic commands"""

    def test_help_flag(self, runner: CliRunner) -> None:
        """Test that --help works"""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Claude Clone" in result.output
        assert "--model" in result.output
        assert "--resume" in result.output

    def test_version_info_in_help(self, runner: CliRunner) -> None:
        """Test that help shows usage info"""
        result = runner.invoke(app, ["--help"])

        assert "AI Coding Assistant" in result.output


class TestCLIOneShotMode:
    """Tests for one-shot mode with prompt argument"""

    @patch("claude_clone.cli.app.run_single_turn")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_oneshot_with_prompt(
        self,
        mock_config_loader: MagicMock,
        mock_run_single_turn: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test one-shot mode executes prompt"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config
        mock_run_single_turn.return_value = "File contents here"

        result = runner.invoke(app, ["read main.py"])

        assert result.exit_code == 0
        mock_run_single_turn.assert_called_once_with(mock_config, "read main.py")
        assert "File contents here" in result.output

    @patch("claude_clone.cli.app.run_single_turn")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_oneshot_empty_response(
        self,
        mock_config_loader: MagicMock,
        mock_run_single_turn: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test one-shot mode with empty response"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config
        mock_run_single_turn.return_value = ""

        result = runner.invoke(app, ["test prompt"])

        assert result.exit_code == 0

    @patch("claude_clone.cli.app.run_single_turn")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_oneshot_error_handling(
        self,
        mock_config_loader: MagicMock,
        mock_run_single_turn: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test one-shot mode error handling"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config
        mock_run_single_turn.side_effect = Exception("API Error")

        result = runner.invoke(app, ["test prompt"])

        assert result.exit_code == 1
        assert "Error" in result.output


class TestCLIModelOption:
    """Tests for --model option"""

    @patch("claude_clone.cli.app.run_single_turn")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_model_option_overrides_config(
        self,
        mock_config_loader: MagicMock,
        mock_run_single_turn: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that --model overrides default model"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config
        mock_run_single_turn.return_value = "response"

        result = runner.invoke(app, ["--model", "gemini-1.5-pro", "test"])

        assert result.exit_code == 0
        mock_config.model_copy.assert_called_once_with(update={"model": "gemini-1.5-pro"})

    @patch("claude_clone.cli.app.run_single_turn")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_model_short_option(
        self,
        mock_config_loader: MagicMock,
        mock_run_single_turn: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that -m short option works"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config
        mock_run_single_turn.return_value = "response"

        result = runner.invoke(app, ["-m", "gemini-1.5-pro", "test"])

        assert result.exit_code == 0
        mock_config.model_copy.assert_called_once()


class TestCLIResumeOption:
    """Tests for --resume option"""

    @patch("claude_clone.cli.app.run_repl")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_resume_shows_not_implemented(
        self,
        mock_config_loader: MagicMock,
        mock_run_repl: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that --resume shows not implemented message"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config

        result = runner.invoke(app, ["--resume"])

        assert "not yet implemented" in result.output


class TestCLIInteractiveMode:
    """Tests for interactive REPL mode"""

    @patch("claude_clone.cli.app.run_repl")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_no_args_starts_repl(
        self,
        mock_config_loader: MagicMock,
        mock_run_repl: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that no arguments starts REPL"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config

        result = runner.invoke(app, [])

        assert result.exit_code == 0
        mock_run_repl.assert_called_once_with(mock_config)

    @patch("claude_clone.cli.app.run_repl")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_repl_keyboard_interrupt(
        self,
        mock_config_loader: MagicMock,
        mock_run_repl: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that KeyboardInterrupt exits cleanly"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config
        mock_run_repl.side_effect = KeyboardInterrupt()

        result = runner.invoke(app, [])

        assert result.exit_code == 0

    @patch("claude_clone.cli.app.run_repl")
    @patch("claude_clone.cli.app.SimpleConfigLoader")
    def test_repl_error_handling(
        self,
        mock_config_loader: MagicMock,
        mock_run_repl: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test REPL error handling"""
        mock_config = MagicMock()
        mock_config.model_copy.return_value = mock_config
        mock_config_loader.return_value.load.return_value = mock_config
        mock_run_repl.side_effect = Exception("Config error")

        result = runner.invoke(app, [])

        assert result.exit_code == 1
        assert "Error" in result.output
