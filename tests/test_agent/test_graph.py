"""Tests for LangGraph Agent"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from claude_clone.agent import AgentState, create_agent
from claude_clone.interfaces import Config


# Test tool for use in tests
@tool
def dummy_read_file(file_path: str) -> str:
    """Read a file and return its contents.

    Args:
        file_path: Path to the file to read
    """
    return f"Contents of {file_path}"


class TestCreateAgent:
    """Tests for create_agent factory function"""

    @pytest.fixture
    def mock_config(self) -> Config:
        """Valid configuration for testing"""
        return Config(
            api_key="test-api-key",
            provider="gemini",
            model="gemini-3.0-flash-preview",
        )

    @patch("claude_clone.agent.graph.create_llm")
    def test_creates_agent_without_tools(
        self, mock_create_llm: MagicMock, mock_config: Config
    ) -> None:
        """Test agent creation without tools"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Hello!")
        mock_create_llm.return_value = mock_llm

        agent = create_agent(mock_config)

        assert agent is not None
        mock_create_llm.assert_called_once_with(mock_config)

    @patch("claude_clone.agent.graph.create_llm")
    def test_creates_agent_with_tools(
        self, mock_create_llm: MagicMock, mock_config: Config
    ) -> None:
        """Test agent creation with tools binds them to LLM"""
        mock_llm = MagicMock()
        mock_llm_with_tools = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_llm_with_tools.invoke.return_value = AIMessage(content="I'll read that file.")
        mock_create_llm.return_value = mock_llm

        agent = create_agent(mock_config, tools=[dummy_read_file])

        assert agent is not None
        mock_llm.bind_tools.assert_called_once_with([dummy_read_file])

    @patch("claude_clone.agent.graph.create_llm")
    def test_agent_invoke_simple_conversation(
        self, mock_create_llm: MagicMock, mock_config: Config
    ) -> None:
        """Test simple conversation without tool calls"""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Hello! How can I help?")
        mock_create_llm.return_value = mock_llm

        agent = create_agent(mock_config)

        # Invoke with a simple message
        result = agent.invoke({"messages": [HumanMessage(content="Hi")]})

        assert "messages" in result
        assert len(result["messages"]) == 2  # User message + AI response
        assert result["messages"][-1].content == "Hello! How can I help?"

    @patch("claude_clone.agent.graph.create_llm")
    def test_agent_invoke_with_tool_call(
        self, mock_create_llm: MagicMock, mock_config: Config
    ) -> None:
        """Test conversation with tool call"""
        # First call: LLM decides to use tool
        tool_call_response = AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_123",
                    "name": "dummy_read_file",
                    "args": {"file_path": "/test.py"},
                }
            ],
        )

        # Second call: LLM responds after seeing tool result
        final_response = AIMessage(content="The file contains: print('hello')")

        mock_llm = MagicMock()
        mock_llm_with_tools = MagicMock()
        mock_llm_with_tools.invoke.side_effect = [tool_call_response, final_response]
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        mock_create_llm.return_value = mock_llm

        agent = create_agent(mock_config, tools=[dummy_read_file])

        result = agent.invoke({"messages": [HumanMessage(content="Read test.py")]})

        # Should have: User -> AI (tool call) -> Tool result -> AI (final)
        assert len(result["messages"]) >= 3
        assert result["messages"][-1].content == "The file contains: print('hello')"


class TestAgentState:
    """Tests for AgentState TypedDict"""

    def test_state_structure(self) -> None:
        """Test AgentState has correct structure"""
        state: AgentState = {
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!"),
            ]
        }

        assert "messages" in state
        assert len(state["messages"]) == 2
