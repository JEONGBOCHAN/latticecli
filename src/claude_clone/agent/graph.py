"""LangGraph Agent - Core conversation flow

Defines the agent workflow using LangGraph's StateGraph.
The flow is: User Input -> LLM -> (optional) Tool Call -> LLM -> Response

Graph Structure:
    START -> call_model -> should_continue? -> call_tools -> call_model -> ...
                                            -> END

State Management:
    - messages: List of conversation messages (HumanMessage, AIMessage, ToolMessage)
    - The state persists across the entire conversation

Usage:
    from claude_clone.agent.graph import create_agent
    from claude_clone.backends import SimpleConfigLoader

    config = SimpleConfigLoader().load()
    agent = create_agent(config)
    result = agent.invoke({"messages": [HumanMessage(content="Hello")]})
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from claude_clone.agent.llm import create_llm
from claude_clone.interfaces import Config


class AgentState(TypedDict):
    """Agent state that persists across conversation

    Attributes:
        messages: Conversation history. LangGraph's add_messages reducer
                  automatically appends new messages instead of replacing.
    """

    messages: Annotated[list[AnyMessage], add_messages]


def create_agent(config: Config, tools: list[BaseTool] | None = None) -> CompiledStateGraph:
    """Create and compile the agent graph

    Creates a ReAct-style agent that can:
    1. Receive user messages
    2. Call LLM to generate responses
    3. Optionally call tools based on LLM decision
    4. Loop until LLM decides to respond without tools

    Args:
        config: Application configuration
        tools: List of LangChain tools to bind. If None, no tools are available.

    Returns:
        Compiled StateGraph ready to invoke

    Example:
        >>> config = Config(api_key="key", provider="gemini", model="gemini-3.0-flash-preview")
        >>> agent = create_agent(config, tools=[read_tool])
        >>> result = agent.invoke({"messages": [HumanMessage(content="Read main.py")]})
        >>> print(result["messages"][-1].content)
    """
    # Create LLM and bind tools if provided
    llm = create_llm(config)
    if tools:
        llm = llm.bind_tools(tools)

    # Define the call_model node
    def call_model(state: AgentState) -> dict:
        """Invoke LLM with current conversation state

        Takes all messages in state and sends to LLM.
        Returns the LLM's response to be added to messages.
        """
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    # Define conditional edge: should we call tools or end?
    def should_continue(state: AgentState) -> str:
        """Determine next step based on LLM response

        If the last message has tool_calls, route to tools node.
        Otherwise, end the conversation turn.

        Returns:
            "tools" to call tools, or END to finish
        """
        last_message = state["messages"][-1]

        # Check if LLM wants to call tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return END

    # Build the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("call_model", call_model)

    # Add tool node if tools are provided
    if tools:
        tool_node = ToolNode(tools)
        graph.add_node("tools", tool_node)

    # Add edges
    graph.add_edge(START, "call_model")

    if tools:
        # After call_model, decide whether to call tools or end
        graph.add_conditional_edges(
            "call_model",
            should_continue,
            {
                "tools": "tools",
                END: END,
            },
        )
        # After tools, always go back to call_model
        graph.add_edge("tools", "call_model")
    else:
        # No tools, just end after call_model
        graph.add_edge("call_model", END)

    # Compile and return
    return graph.compile()
