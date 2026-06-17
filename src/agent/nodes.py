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


def timed_node(node_name):
    def decorator(func):
        def wrapper(state: AgentState) -> AgentState:
            start_time = time.time()
            metadata = dict(state.get("metadata", {})) if state.get("metadata") is not None else {}
            if "execution_trace" not in metadata:
                metadata["execution_trace"] = []
            try:
                res_state = func(state)
                if res_state is None:
                    res_state = dict(state)
                else:
                    res_state = dict(res_state)
                end_time = time.time()
                metadata["execution_trace"].append({
                    "node": node_name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": round(end_time - start_time, 3),
                    "status": "success",
                    "error": None
                })
                res_state["metadata"] = metadata
                return res_state
            except Exception as e:
                end_time = time.time()
                metadata["execution_trace"].append({
                    "node": node_name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": round(end_time - start_time, 3),
                    "status": "error",
                    "error": str(e)
                })
                new_state = dict(state)
                new_state["metadata"] = metadata
                raise e
        return wrapper
    return decorator

@timed_node("planner_node")
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

@timed_node("tool_executor")
def tool_executor(state: AgentState) -> AgentState:
    """
    Executes the tools identified by the planner node.
    """
    LOGGER.info("[NODE: tool_executor] Executing tools...")
    tool_calls = state.get("tool_calls", [])
    tool_results = list(state.get("tool_results", []))
    messages = list(state.get("messages", []))
    reasoning_steps = list(state.get("reasoning_steps", []))
    metadata = dict(state.get("metadata", {})) if state.get("metadata") is not None else {}
    tool_traces = list(metadata.get("tool_traces", []))
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        reasoning_steps.append(f"Executing tool '{tool_name}' with args {tool_args}")
        tool_start = time.time()
        status = "success"
        error_msg = None
        
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
                status = "error"
                error_msg = str(e)
        else:
            LOGGER.warning("[NODE: tool_executor] Unknown tool: %s", tool_name)
            result = {"error": f"Unknown tool name: {tool_name}"}
            reasoning_steps.append(f"Tool execution skipped: Unknown tool '{tool_name}'")
            status = "error"
            error_msg = f"Unknown tool: {tool_name}"
            
        tool_duration = round(time.time() - tool_start, 3)
        tool_traces.append({
            "tool": tool_name,
            "start_time": tool_start,
            "duration": tool_duration,
            "status": status,
            "error": error_msg
        })
        
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
        
    metadata["tool_traces"] = tool_traces
    return {
        **state,
        "messages": messages,
        "tool_results": tool_results,
        "reasoning_steps": reasoning_steps,
        "metadata": metadata
    }

@timed_node("reasoning_node")
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

@timed_node("response_node")
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

@timed_node("memory_retrieval_node")
def memory_retrieval_node(state: AgentState) -> AgentState:
    """
    Retrieves semantic user memories from Qdrant and injects them along with the user profile.
    """
    LOGGER.info("[NODE: memory_retrieval_node] Querying semantic memories...")
    user_query = state.get("user_query")
    session_id = state.get("session_id", "default")
    
    # 1. Search memory collection
    memories = memory_store.search_memories(user_query, session_id=session_id, limit=5)
    
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

def extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Search for first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
        raise

@timed_node("memory_update_node")
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
        
        try:
            updates = extract_json(content)
        except Exception as json_err:
            LOGGER.warning("[NODE: memory_update_node] Failed parsing extracted JSON payload: %s", str(json_err))
            updates = {"memories": [], "profile_updates": {}}
            
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

