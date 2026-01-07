"""REPL Loop - Main conversation loop

Implements the Read-Eval-Print Loop that:
1. Gets user input
2. Sends to LangGraph agent
3. Displays response with tool calls

Usage:
    from claude_clone.repl.loop import run_repl
    from claude_clone.interfaces import Config

    config = Config(api_key="key", provider="gemini", model="gemini-2.0-flash")
    run_repl(config)
"""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from claude_clone.agent.graph import create_agent


def _extract_text_content(content: Any) -> str:
    """Extract text content from AIMessage content

    Handles different content formats:
    - String: Returns as-is
    - List of content blocks: Extracts and joins text from each block

    Args:
        content: AIMessage.content (str or list of dicts)

    Returns:
        Extracted text content as string
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                texts.append(block["text"])
            elif isinstance(block, str):
                texts.append(block)
        return "\n".join(texts)

    return str(content)


from claude_clone.agent.tools import read_tool
from claude_clone.interfaces import Config
from claude_clone.prompts import SYSTEM_PROMPT
from claude_clone.repl.input import get_user_input
from claude_clone.repl.output import (
    print_error,
    print_goodbye,
    print_info,
    print_response,
    print_tool_call,
    print_tool_result,
    print_welcome,
)


def run_repl(config: Config) -> None:
    """Run the main REPL loop

    Creates the agent and runs the conversation loop until
    the user exits with Ctrl+D or Ctrl+C.

    Args:
        config: Application configuration with API key and model settings
    """
    # Create agent with tools
    tools = [read_tool]
    agent = create_agent(config, tools=tools)

    # Initialize conversation with system prompt
    messages: list[SystemMessage | HumanMessage | AIMessage | ToolMessage] = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]

    print_welcome()

    while True:
        try:
            # Get user input
            user_input = get_user_input()

            # Skip empty input
            if not user_input:
                continue

            # Add user message to conversation
            messages.append(HumanMessage(content=user_input))

            # Invoke agent
            print_info("Thinking...")
            result = agent.invoke({"messages": messages})

            # Process response messages
            response_messages = result["messages"]

            # Find new messages (after our input)
            new_messages = response_messages[len(messages) :]

            # Display each new message
            for msg in new_messages:
                if isinstance(msg, AIMessage):
                    # Check for tool calls
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            print_tool_call(tool_call["name"], tool_call["args"])
                    # Print text content if any
                    if msg.content:
                        print_response(_extract_text_content(msg.content))
                elif isinstance(msg, ToolMessage):
                    # Print tool result
                    print_tool_result(msg.name or "tool", str(msg.content))

            # Update our message history
            messages = response_messages

        except KeyboardInterrupt:
            # Ctrl+C - cancel current input
            print_info("\nCancelled")
            continue

        except EOFError:
            # Ctrl+D - exit
            print_goodbye()
            break

        except Exception as e:
            print_error(str(e))
            # Continue the loop, don't crash


def run_single_turn(config: Config, user_input: str) -> str:
    """Run a single conversation turn

    Useful for CLI one-shot mode or testing.

    Args:
        config: Application configuration
        user_input: User's input message

    Returns:
        AI response text

    Raises:
        Exception: If agent invocation fails
    """
    # Create agent with tools
    tools = [read_tool]
    agent = create_agent(config, tools=tools)

    # Build messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ]

    # Invoke agent
    result = agent.invoke({"messages": messages})

    # Extract final response
    response_messages = result["messages"]
    final_message = response_messages[-1]

    if isinstance(final_message, AIMessage) and final_message.content:
        return _extract_text_content(final_message.content)

    return ""
