import logging
from langgraph.graph import StateGraph, START, END

from src.agent.state import AgentState
from src.agent.nodes import (
    planner_node,
    tool_executor,
    reasoning_node,
    response_node,
    memory_retrieval_node,
    memory_update_node
)
from src.agent.router import tool_router

LOGGER = logging.getLogger(__name__)

def create_agent_graph():
    """
    Creates and compiles the StateGraph for the Spotify Agent.
    """
    # Initialize the graph with the AgentState schema
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("memory_retrieval_node", memory_retrieval_node)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("tool_executor", tool_executor)
    workflow.add_node("reasoning_node", reasoning_node)
    workflow.add_node("memory_update_node", memory_update_node)
    workflow.add_node("response_node", response_node)
    
    # Define edges
    # START -> memory_retrieval_node -> planner_node
    workflow.add_edge(START, "memory_retrieval_node")
    workflow.add_edge("memory_retrieval_node", "planner_node")
    
    # Conditional edge from planner_node using the tool_router
    workflow.add_conditional_edges(
        "planner_node",
        tool_router,
        {
            "tool_executor": "tool_executor",
            "reasoning_node": "reasoning_node"
        }
    )
    
    # tool_executor -> reasoning_node
    workflow.add_edge("tool_executor", "reasoning_node")
    
    # reasoning_node -> memory_update_node -> response_node
    workflow.add_edge("reasoning_node", "memory_update_node")
    workflow.add_edge("memory_update_node", "response_node")
    
    # response_node -> END
    workflow.add_edge("response_node", END)
    
    # Compile the graph
    return workflow.compile()

# Default compiled graph instance
agent_graph = create_agent_graph()
