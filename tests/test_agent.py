import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, ToolMessage

from src.agent.state import AgentState
from src.agent.nodes import (
    planner_node,
    tool_executor,
    reasoning_node,
    response_node,
    memory_retrieval_node,
    memory_update_node
)
from src.agent.graph import agent_graph


def test_planner_node_with_tools():
    # Setup state
    state: AgentState = {
        "messages": [],
        "user_query": "Find energetic Afro House tracks",
        "tool_calls": [],
        "tool_results": [],
        "final_response": "",
        "reasoning_steps": [],
        "session_id": "test_session",
        "conversation_history": [],
        "selected_tools": [],
        "metadata": {}
    }

    # Mock response with tool calls
    mock_ai_response = AIMessage(
        content="I will search for Afro House tracks.",
        tool_calls=[{
            "name": "search_tracks_tool",
            "args": {"query": "Afro House"},
            "id": "call_123",
            "type": "tool_call"
        }]
    )

    with patch("src.agent.nodes.llm_with_tools") as mock_llm_with_tools:
        mock_llm_with_tools.invoke.return_value = mock_ai_response

        new_state = planner_node(state)

        # Verify tool calls and selected tools are populated
        assert new_state["tool_calls"] == [{
            "name": "search_tracks_tool",
            "args": {"query": "Afro House"},
            "id": "call_123",
            "type": "tool_call"
        }]
        assert "search_tracks_tool" in new_state["selected_tools"]
        assert len(new_state["messages"]) == 1
        assert isinstance(new_state["messages"][0], AIMessage)


def test_planner_node_no_tools():
    # Setup state
    state: AgentState = {
        "messages": [],
        "user_query": "What is Spotify?",
        "tool_calls": [],
        "tool_results": [],
        "final_response": "",
        "reasoning_steps": [],
        "session_id": "test_session",
        "conversation_history": [],
        "selected_tools": [],
        "metadata": {}
    }

    # Mock response with no tool calls
    mock_ai_response = AIMessage(
        content="Spotify is a digital music, podcast, and video service.",
        tool_calls=[]
    )

    with patch("src.agent.nodes.llm_with_tools") as mock_llm_with_tools:
        mock_llm_with_tools.invoke.return_value = mock_ai_response

        new_state = planner_node(state)

        # Verify no tools were selected
        assert new_state["tool_calls"] == []
        assert new_state["selected_tools"] == []
        assert len(new_state["messages"]) == 1


def test_tool_executor():
    # Setup state with tool calls ready to be executed
    state: AgentState = {
        "messages": [],
        "user_query": "Find energetic Afro House tracks",
        "tool_calls": [{
            "name": "search_tracks_tool",
            "args": {"query": "Afro House"},
            "id": "call_123"
        }],
        "tool_results": [],
        "final_response": "",
        "reasoning_steps": [],
        "session_id": "test_session",
        "conversation_history": [],
        "selected_tools": ["search_tracks_tool"],
        "metadata": {}
    }

    # Mock the underlying tool's search_tracks result
    mock_results = [{"name": "Bam Bam", "artist": "Sister Nancy", "id": "123"}]

    with patch("src.agent.tools.search_tracks") as mock_search:
        mock_search.return_value = mock_results

        new_state = tool_executor(state)

        # Verify tool result was recorded
        assert len(new_state["tool_results"]) == 1
        assert new_state["tool_results"][0]["tool_name"] == "search_tracks_tool"
        assert new_state["tool_results"][0]["result"] == mock_results

        # Verify a ToolMessage was added
        assert len(new_state["messages"]) == 1
        assert isinstance(new_state["messages"][0], ToolMessage)
        assert new_state["messages"][0].tool_call_id == "call_123"


def test_reasoning_node():
    state: AgentState = {
        "messages": [],
        "user_query": "Find energetic Afro House tracks",
        "tool_calls": [],
        "tool_results": [{
            "tool_name": "search_tracks_tool",
            "args": {"query": "Afro House"},
            "result": [{"name": "Bam Bam", "artist": "Sister Nancy"}]
        }],
        "final_response": "",
        "reasoning_steps": ["Step 1"],
        "session_id": "test_session",
        "conversation_history": [],
        "selected_tools": ["search_tracks_tool"],
        "metadata": {}
    }

    mock_ai_response = AIMessage(content="Here are the best Afro House tracks...")

    with patch("src.agent.nodes.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_ai_response

        new_state = reasoning_node(state)

        # Verify final response is set
        assert new_state["final_response"] == "Here are the best Afro House tracks..."
        assert len(new_state["messages"]) == 1


def test_response_node():
    state: AgentState = {
        "messages": [],
        "user_query": "Find energetic Afro House tracks",
        "tool_calls": [],
        "tool_results": [],
        "final_response": "Here are the best Afro House tracks...",
        "reasoning_steps": ["Step 1", "Step 2"],
        "session_id": "test_session",
        "conversation_history": [],
        "selected_tools": ["search_tracks_tool"],
        "metadata": {}
    }

    new_state = response_node(state)

    # Verify formatting applied
    assert "## 🎵 Spotify Music Copilot Response" in new_state["final_response"]
    assert "*⚡ Powered by Spotify Music Copilot Tools: `search_tracks_tool`*" in new_state["final_response"]
    assert "🔍 Reasoning Trace & Executed Steps" in new_state["final_response"]
    assert len(new_state["messages"]) == 1


def test_full_graph_workflow_no_tools():
    # Setup inputs for graph invoke
    inputs = {
        "messages": [],
        "user_query": "What is Spotify?",
        "tool_calls": [],
        "tool_results": [],
        "final_response": "",
        "reasoning_steps": [],
        "session_id": "test_session",
        "conversation_history": [],
        "selected_tools": [],
        "metadata": {}
    }

    # Mock planner and reasoning responses
    mock_planner_response = AIMessage(content="Let's explain what Spotify is.", tool_calls=[])
    mock_reasoning_response = AIMessage(content="Spotify is a popular music streaming service.")

    with patch("src.agent.nodes.llm_with_tools") as mock_llm_with_tools, \
         patch("src.agent.nodes.llm") as mock_llm:
        mock_llm_with_tools.invoke.return_value = mock_planner_response
        mock_llm.invoke.return_value = mock_reasoning_response

        res = agent_graph.invoke(inputs)

        # Verify flow reached the end and formatted final response
        assert "## 🎵 Spotify Music Copilot Response" in res["final_response"]
        assert "Spotify is a popular music streaming service." in res["final_response"]


def test_memory_pipeline_integration():
    session_id = "test_memory_session_123"
    from src.agent.nodes import memory_store
    memory_store.clear(session_id)
    
    # 1. Mock the LLM preference extractor response
    mock_extractor_response = AIMessage(
        content='''
        {
            "memories": ["User loves Afro House music"],
            "profile_updates": {
                "favorite_genres": ["afro house"],
                "favorite_artists": [],
                "favorite_moods": []
            }
        }
        '''
    )
    
    state: AgentState = {
        "messages": [],
        "user_query": "I love Afro House",
        "tool_calls": [],
        "tool_results": [],
        "final_response": "I have noted your preference for Afro House music.",
        "reasoning_steps": [],
        "session_id": session_id,
        "conversation_history": [],
        "selected_tools": [],
        "metadata": {},
        "retrieved_memories": [],
        "user_profile": {}
    }
    
    with patch("src.agent.nodes.llm") as mock_llm:
        mock_llm.invoke.return_value = mock_extractor_response
        
        # Run memory update
        updated_state = memory_update_node(state)
        assert "Stored long-term preference: 'User loves Afro House music'" in updated_state["reasoning_steps"]
        
    # 2. Verify retrieval in a subsequent turn
    retrieval_state: AgentState = {
        "messages": [],
        "user_query": "What should I listen to?",
        "tool_calls": [],
        "tool_results": [],
        "final_response": "",
        "reasoning_steps": [],
        "session_id": session_id,
        "conversation_history": [],
        "selected_tools": [],
        "metadata": {},
        "retrieved_memories": [],
        "user_profile": {}
    }
    
    retrieved_state = memory_retrieval_node(retrieval_state)
    
    # Check memories were successfully retrieved and profile was loaded
    assert len(retrieved_state["retrieved_memories"]) > 0
    assert retrieved_state["retrieved_memories"][0]["text"] == "User loves Afro House music"
    assert "afro house" in retrieved_state["user_profile"]["favorite_genres"]
    
    # Clean up memory store for this session
    from src.agent.nodes import memory_store
    memory_store.clear(session_id)

