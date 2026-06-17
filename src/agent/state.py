from typing import TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_query: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    final_response: str
    reasoning_steps: List[str]
    session_id: str
    conversation_history: List[BaseMessage]
    selected_tools: List[str]
    metadata: Dict[str, Any]
    retrieved_memories: List[Dict[str, Any]]
    user_profile: Dict[str, Any]

