import os
import time
import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq
from src.agent.state import AgentState
from src.agent.tools import ALL_TOOLS, TOOLS_BY_NAME
from src.agent.prompts import (
    PLANNER_SYSTEM_PROMPT,
    REASONING_SYSTEM_PROMPT,
    RESPONSE_SYSTEM_PROMPT,
    MEMORY_EXTRACTOR_PROMPT
)
from src.agent.memory import QdrantMemoryStore

LOGGER = logging.getLogger(__name__)

# Initialize LLM globally using Groq
api_key = os.getenv("GROQ_API_KEY") or "PLACEHOLDER"
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=api_key,
    temperature=0.2
)

# Bind tools globally - mandatory requirement
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Initialize Qdrant Memory Store globally
memory_store = QdrantMemoryStore(location="localhost", port=6333)


def planner_node(state: AgentState) -> AgentState:
    """
    Analyzes user intent, logs reasoning steps, and decides if any tool calls are required.
    """
    LOGGER.info("[NODE: planner_node] Starting execution...")
    user_query = state.get("user_query")
    messages = state.get("messages", [])
    
    # 1. Prepare tool descriptions for the planner prompt
    tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in ALL_TOOLS])
    system_content = PLANNER_SYSTEM_PROMPT.format(
        tool_descriptions=tool_descriptions,
        retrieved_memories=str(state.get("retrieved_memories", [])),
        user_profile=str(state.get("user_profile", {}))
    )
    
    # 3. Create context for the planner
    planner_messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_query)
    ]
    
    try:
        response = llm_with_tools.invoke(planner_messages)
        # Update messages history
        updated_messages = list(messages)
        updated_messages.append(response)
        
        # Track reasoning trace
        reasoning_steps = list(state.get("reasoning_steps", []))
        reasoning_steps.append(f"Planner analyzed query: '{user_query}' and generated response.")
        
        # Extract selected tools if any
        selected_tools = []
        if response.tool_calls:
            selected_tools = [tc["name"] for tc in response.tool_calls]
            reasoning_steps.append(f"Planner identified tools to call: {selected_tools}")
        else:
            reasoning_steps.append("Planner decided no tools are required.")
            
        return {
            **state,
            "messages": updated_messages,
            "selected_tools": selected_tools,
            "reasoning_steps": reasoning_steps,
            "tool_calls": response.tool_calls or []
        }
    except Exception as e:
        LOGGER.error("[NODE: planner_node] Failed invoking LLM: %s", str(e))
        fallback_msg = AIMessage(content=f"Error analyzing query: {str(e)}")
        return {
            **state,
            "messages": messages + [fallback_msg],
            "reasoning_steps": state.get("reasoning_steps", []) + [f"Planner node error: {str(e)}"],
            "tool_calls": [],
            "selected_tools": []
        }

def tool_executor(state: AgentState) -> AgentState:
    """
    Executes the tools identified by the planner node.
    """
    LOGGER.info("[NODE: tool_executor] Executing tools...")
    tool_calls = state.get("tool_calls", [])
    tool_results = list(state.get("tool_results", []))
    messages = list(state.get("messages", []))
    reasoning_steps = list(state.get("reasoning_steps", []))
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        reasoning_steps.append(f"Executing tool '{tool_name}' with args {tool_args}")
        
        if tool_name in TOOLS_BY_NAME:
            tool_func = TOOLS_BY_NAME[tool_name]
            try:
                # Invoke the LangChain tool wrapper
                result = tool_func.invoke(tool_args)
                reasoning_steps.append(f"Tool '{tool_name}' completed successfully.")
            except Exception as e:
                LOGGER.error("[NODE: tool_executor] Tool '%s' failed: %s", tool_name, str(e))
                result = {"error": f"Tool execution failed: {str(e)}"}
                reasoning_steps.append(f"Tool '{tool_name}' failed: {str(e)}")
        else:
            LOGGER.warning("[NODE: tool_executor] Unknown tool: %s", tool_name)
            result = {"error": f"Unknown tool name: {tool_name}"}
            reasoning_steps.append(f"Tool execution skipped: Unknown tool '{tool_name}'")
            
        tool_results.append({
            "tool_name": tool_name,
            "args": tool_args,
            "result": result
        })
        
        # Append ToolMessage to keep graph trace intact
        messages.append(ToolMessage(
            content=str(result),
            tool_call_id=tool_id,
            name=tool_name
        ))
        
    return {
        **state,
        "messages": messages,
        "tool_results": tool_results,
        "reasoning_steps": reasoning_steps
    }

def reasoning_node(state: AgentState) -> AgentState:
    """
    Synthesizes search results, track details, and playlists into a coherent explanation.
    """
    LOGGER.info("[NODE: reasoning_node] Synthesizing results...")
    user_query = state.get("user_query")
    tool_results = state.get("tool_results", [])
    reasoning_steps = list(state.get("reasoning_steps", []))
    
    # 1. Format tool results for model review
    formatted_results = ""
    for idx, tr in enumerate(tool_results):
        formatted_results += f"\n--- Result {idx+1} ({tr['tool_name']}) ---\n"
        formatted_results += f"Args: {tr['args']}\n"
        formatted_results += f"Result: {tr['result']}\n"
        
    system_prompt = REASONING_SYSTEM_PROMPT.format(
        user_query=user_query,
        tool_results=formatted_results or "No tool outputs (direct conversation)."
    )
    
    # 2. Invoke LLM for synthesis
    reasoning_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query)
    ]
    
    try:
        response = llm.invoke(reasoning_messages)
        reasoning_steps.append("Reasoning node completed synthesis of results.")
        return {
            **state,
            "messages": state.get("messages", []) + [response],
            "reasoning_steps": reasoning_steps,
            "final_response": response.content
        }
    except Exception as e:
        LOGGER.error("[NODE: reasoning_node] Failed invoking LLM: %s", str(e))
        fallback_content = f"Failed to synthesize music details. Tool results: {formatted_results}"
        return {
            **state,
            "messages": state.get("messages", []) + [AIMessage(content=fallback_content)],
            "reasoning_steps": reasoning_steps + [f"Reasoning node error: {str(e)}"],
            "final_response": fallback_content
        }

def response_node(state: AgentState) -> AgentState:
    """
    Applies high-end visual markdown formatting and lists tools cited.
    """
    LOGGER.info("[NODE: response_node] Preparing final response...")
    final_response = state.get("final_response", "")
    selected_tools = state.get("selected_tools", [])
    reasoning_steps = state.get("reasoning_steps", [])
    
    # 1. Build citation text
    citation_text = ""
    if selected_tools:
        citation_text = "\n\n---\n*⚡ Powered by Spotify Music Copilot Tools: " + ", ".join([f"`{t}`" for t in set(selected_tools)]) + "*"
        
    # Format reasoning steps cleanly
    steps_md = "".join([f"- {step}\n" for step in reasoning_steps])
    
    formatted_content = f"""## 🎵 Spotify Music Copilot Response

{final_response}{citation_text}

<details>
<summary><b>🔍 Reasoning Trace & Executed Steps</b></summary>

{steps_md}
</details>
"""
    
    return {
        **state,
        "final_response": formatted_content,
        "messages": state.get("messages", []) + [AIMessage(content=formatted_content)]
    }

def memory_retrieval_node(state: AgentState) -> AgentState:
    """
    Retrieves semantic user memories from Qdrant and injects them along with the user profile.
    """
    LOGGER.info("[NODE: memory_retrieval_node] Querying semantic memories...")
    user_query = state.get("user_query")
    session_id = state.get("session_id", "default")
    
    # 1. Search memory collection
    memories = memory_store.search_memories(user_query, limit=5)
    
    # 2. Get user profile
    profile = memory_store.get_profile(session_id)
    
    reasoning_steps = list(state.get("reasoning_steps", []))
    reasoning_steps.append(f"Retrieved {len(memories)} semantic memories and loaded active user profile.")
    
    return {
        **state,
        "retrieved_memories": memories,
        "user_profile": profile,
        "reasoning_steps": reasoning_steps
    }

import json

def memory_update_node(state: AgentState) -> AgentState:
    """
    Evaluates the conversation context, extracts user preferences and profile updates,
    and upserts them to the Qdrant long-term memory store.
    """
    LOGGER.info("[NODE: memory_update_node] Evaluating conversation for memory extraction...")
    user_query = state.get("user_query")
    final_response = state.get("final_response")
    session_id = state.get("session_id", "default")
    reasoning_steps = list(state.get("reasoning_steps", []))
    
    # Context to evaluate
    context = f"User Query: {user_query}\nAssistant Response: {final_response}"
    
    messages = [
        SystemMessage(content=MEMORY_EXTRACTOR_PROMPT),
        HumanMessage(content=context)
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Clean JSON if wrapped in markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        updates = json.loads(content)
        
        # 1. Persist new semantic memories
        new_memories = updates.get("memories", [])
        for memory in new_memories:
            LOGGER.info("[MEMORY STORED] %s", memory)
            memory_store.add_memory(session_id, memory, category="preference")
            reasoning_steps.append(f"Stored long-term preference: '{memory}'")
            
        # 2. Update user profile
        profile = memory_store.get_profile(session_id)
        profile_updates = updates.get("profile_updates", {})
        
        # Merge lists
        for k in ["favorite_genres", "favorite_artists", "favorite_moods"]:
            if k in profile_updates and profile_updates[k]:
                merged = list(set(profile.get(k, []) + profile_updates[k]))
                profile[k] = merged
                
        # Update playlist history if user generated a playlist
        selected_tools = state.get("selected_tools", [])
        if "playlist_generation_tool" in selected_tools or "create_playlist_tool" in selected_tools:
            profile["playlist_history"].append({
                "query": user_query,
                "timestamp": time.time()
            })
            
        # Save updated profile
        memory_store.save_profile(session_id, profile)
        reasoning_steps.append("Updated and synchronized active user profile in vector DB.")
        
    except Exception as e:
        LOGGER.error("[NODE: memory_update_node] Failed to extract/update memory: %s", str(e))
        reasoning_steps.append(f"Memory update node warning: {str(e)}")
        
    return {
        **state,
        "reasoning_steps": reasoning_steps
    }

