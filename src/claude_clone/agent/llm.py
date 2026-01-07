"""LLM Factory - Creates LLM instances based on configuration

Factory pattern to create appropriate LLM based on provider setting.
MVP supports Gemini only, future versions will support multiple providers.

Usage:
    from claude_clone.agent.llm import create_llm
    from claude_clone.backends import SimpleConfigLoader

    config = SimpleConfigLoader().load()
    llm = create_llm(config)
"""

from langchain_google_genai import ChatGoogleGenerativeAI

from claude_clone.interfaces import Config


class LLMCreationError(Exception):
    """Error during LLM creation"""

    pass


def create_llm(config: Config) -> ChatGoogleGenerativeAI:
    """Create LLM instance from configuration

    Factory function that creates the appropriate LLM based on
    the provider setting in config.

    Args:
        config: Application configuration containing provider, model, api_key

    Returns:
        LLM instance (ChatGoogleGenerativeAI for MVP)

    Raises:
        LLMCreationError: When provider is unsupported or creation fails

    Example:
        >>> config = Config(api_key="key", provider="gemini", model="gemini-3.0-flash-preview")
        >>> llm = create_llm(config)
        >>> response = llm.invoke("Hello!")
    """
    if config.provider != "gemini":
        raise LLMCreationError(
            f"Unsupported provider: {config.provider}\n"
            "MVP only supports 'gemini'. "
            "Future versions will support: anthropic, openai, ollama"
        )

    if not config.api_key:
        raise LLMCreationError(
            "API key is required. "
            "Set GOOGLE_API_KEY environment variable or configure in config.toml"
        )

    try:
        return ChatGoogleGenerativeAI(
            model=config.model,
            google_api_key=config.api_key,
            # Streaming disabled for MVP, enable in future
            # streaming=True,
        )
    except Exception as e:
        raise LLMCreationError(f"Failed to create LLM: {e}") from e
