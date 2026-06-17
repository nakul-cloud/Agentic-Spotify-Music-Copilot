from typing import Literal
from langchain_core.messages import AIMessage
from src.agent.state import AgentState

def tool_router(state: AgentState) -> Literal["tool_executor", "reasoning_node"]:
    """
    Inspects the last message in the state. If it contains tool calls,
    routes to tool_executor. Otherwise, routes to reasoning_node.
    """
    messages = state.get("messages", [])
    if not messages:
        return "reasoning_node"
    
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_executor"
        
    return "reasoning_node"
