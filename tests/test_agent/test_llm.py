"""Tests for LLM Factory"""

from unittest.mock import MagicMock, patch

import pytest

from claude_clone.agent import LLMCreationError, create_llm
from claude_clone.interfaces import Config


class TestCreateLLM:
    """Tests for create_llm factory function"""

    def test_unsupported_provider_raises_error(self) -> None:
        """Test that unsupported provider raises LLMCreationError"""
        config = Config(
            api_key="test-key",
            provider="anthropic",  # Not supported in MVP
            model="claude-3-opus",
        )

        with pytest.raises(LLMCreationError) as exc_info:
            create_llm(config)

        assert "Unsupported provider" in str(exc_info.value)
        assert "anthropic" in str(exc_info.value)

    def test_missing_api_key_raises_error(self) -> None:
        """Test that missing API key raises LLMCreationError"""
        config = Config(
            api_key=None,
            provider="gemini",
            model="gemini-3-flash-preview",
        )

        with pytest.raises(LLMCreationError) as exc_info:
            create_llm(config)

        assert "API key is required" in str(exc_info.value)

    @patch("claude_clone.agent.llm.ChatGoogleGenerativeAI")
    def test_creates_gemini_llm_with_valid_config(
        self, mock_chat_class: MagicMock
    ) -> None:
        """Test that valid config creates ChatGoogleGenerativeAI instance"""
        mock_llm = MagicMock()
        mock_chat_class.return_value = mock_llm

        config = Config(
            api_key="test-api-key",
            provider="gemini",
            model="gemini-3-flash-preview",
        )

        result = create_llm(config)

        # Verify ChatGoogleGenerativeAI was called with correct args
        mock_chat_class.assert_called_once_with(
            model="gemini-3-flash-preview",
            google_api_key="test-api-key",
        )
        assert result == mock_llm

    @patch("claude_clone.agent.llm.ChatGoogleGenerativeAI")
    def test_wraps_creation_exception(self, mock_chat_class: MagicMock) -> None:
        """Test that exceptions during LLM creation are wrapped"""
        mock_chat_class.side_effect = ValueError("Invalid API key format")

        config = Config(
            api_key="bad-key",
            provider="gemini",
            model="gemini-3-flash-preview",
        )

        with pytest.raises(LLMCreationError) as exc_info:
            create_llm(config)

        assert "Failed to create LLM" in str(exc_info.value)
