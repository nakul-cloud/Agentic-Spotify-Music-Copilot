import streamlit as st
import os
import uuid
import time
from langchain_core.messages import HumanMessage, AIMessage
from src.agent.graph import agent_graph
from src.agent.nodes import memory_store
from qdrant_client.http import models

# -------------------------------------------------------------
# Premium Spotify-Style UI Config & Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="Spotify Agentic Copilot & Studio",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Glassmorphism & Spotify Theme
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 1px solid #282828;
    }
    
    /* Headers styling */
    h1, h2, h3, h4, h5 {
        color: #1DB954 !important; /* Spotify Green */
        font-weight: 800;
    }
    
    /* Card/Message container */
    .chat-bubble {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }
    
    .user-bubble {
        border-left: 4px solid #1DB954;
    }
    
    .agent-bubble {
        border-left: 4px solid #8E44AD;
    }
    
    /* Buttons custom styling */
    .stButton>button {
        background-color: #1DB954 !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 0.5rem 2rem !important;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px rgba(29, 185, 84, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Session Initialization
# -------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "trace_history" not in st.session_state:
    st.session_state["trace_history"] = []
if "latest_trace" not in st.session_state:
    st.session_state["latest_trace"] = None
if "latest_tool_traces" not in st.session_state:
    st.session_state["latest_tool_traces"] = []
if "tool_analytics" not in st.session_state:
    st.session_state["tool_analytics"] = {}

# Sidebar options
st.sidebar.title("🎵 Spotify Copilot")
st.sidebar.markdown("### Agent Settings")
model_selection = st.sidebar.selectbox("LLM Orchestrator", ["llama-3.3-70b-versatile (Groq)"])

# Keep input session linked to st.session_state["session_id"]
session_input = st.sidebar.text_input("Session ID", value=st.session_state["session_id"])
if session_input != st.session_state["session_id"]:
    st.session_state["session_id"] = session_input
    # Clear conversation history for new session
    st.session_state["chat_history"] = []
    st.session_state["latest_trace"] = None
    st.session_state["latest_tool_traces"] = []

st.sidebar.markdown("---")
st.sidebar.markdown("### Suggested Prompts")
prompts = [
    "Create a sunset Afro House playlist with energetic vocals and explain why each track fits.",
    "Compare the audio features of Calvin Harris and Black Coffee.",
    "Generate a chill ambient focus playlist for late-night coding.",
    "Recommend tracks similar to Illenium and Virtual Riot."
]

selected_prompt = None
for p in prompts:
    if st.sidebar.button(p, key=p):
        selected_prompt = p

# Sidebar footer
st.sidebar.info("Designed with LangGraph, Groq, and Spotify APIs.")

# -------------------------------------------------------------
# Main Layout
# -------------------------------------------------------------
st.title("🎵 Spotify Agent Studio")
st.markdown("##### *A premium, observable LangGraph AI Music Assistant tracking agent reasoning, memory recall, and tool stats in real-time.*")
st.markdown("---")

# -------------------------------------------------------------
# Streamlit Panels (Tabs)
# -------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Chat Copilot",
    "📊 Execution Timeline",
    "📈 Tool Analytics",
    "🧠 Long-Term Memory",
    "🩺 System Health"
])

# -------------------------------------------------------------
# Tab 1: Chat Copilot
# -------------------------------------------------------------
with tab1:
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state["chat_history"]:
            st.markdown(
                """
                <div style="text-align: center; padding: 3rem; color: #888888;">
                    <h3>Welcome to Spotify Agent Studio!</h3>
                    <p>Ask a question or select a suggested prompt from the sidebar to begin.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        for message in st.session_state["chat_history"]:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-bubble user-bubble"><b>You:</b><br>{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble agent-bubble">{message["content"]}</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# Tab 2: Execution Graph / Timeline
# -------------------------------------------------------------
with tab2:
    st.subheader("🔍 Chronological Agent Execution Timeline")
    
    if st.session_state["latest_trace"] is None:
        st.info("No queries executed in this session yet. Ask a question to see the execution trace!")
    else:
        trace = st.session_state["latest_trace"]
        st.markdown(f"**Target User Query:** `{trace['user_query']}`")
        
        nodes = trace["nodes"]
        all_steps = []
        for n in nodes:
            all_steps.append({
                "type": "node",
                "name": n["node"],
                "start_time": n["start_time"],
                "duration": n["duration"],
                "status": n["status"],
                "error": n["error"]
            })
            
        latest_tool_traces = st.session_state.get("latest_tool_traces", [])
        for t in latest_tool_traces:
            all_steps.append({
                "type": "tool",
                "name": t["tool"],
                "start_time": t["start_time"],
                "duration": t["duration"],
                "status": t["status"],
                "error": t["error"]
            })
            
        # Sort chronologically by start time
        all_steps = sorted(all_steps, key=lambda x: x["start_time"])
        
        for step in all_steps:
            time_str = time.strftime("%H:%M:%S", time.localtime(step["start_time"]))
            color = "#1DB954" if step["status"] == "success" else "#E74C3C"
            
            if step["type"] == "node":
                st.markdown(
                    f"""
                    <div style="margin-left: 10px; border-left: 3px solid {color}; padding-left: 15px; margin-bottom: 15px;">
                        <span style="color: #888888; font-size: 0.85rem;">{time_str}</span> &nbsp;&nbsp;
                        <b style="font-size: 1.1rem; color: #1DB954;">⚙️ {step['name']}</b> &nbsp;
                        <span style="background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{step['duration']}s</span>
                        {f'<br><span style="color: red; font-size: 0.9rem;">Error: {step["error"]}</span>' if step["error"] else ''}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="margin-left: 40px; border-left: 3px dashed #8E44AD; padding-left: 15px; margin-bottom: 15px;">
                        <span style="color: #888888; font-size: 0.85rem;">{time_str}</span> &nbsp;&nbsp;
                        <b style="font-size: 1rem; color: #8E44AD;">⚡ Tool: {step['name']}</b> &nbsp;
                        <span style="background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{step['duration']}s</span>
                        {f'<br><span style="color: red; font-size: 0.9rem;">Error: {step["error"]}</span>' if step["error"] else ''}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        # Draw a beautiful flow diagram
        st.markdown("### 🗺️ Node Execution Flow Highlight")
        flow_cols = st.columns(6)
        flow_nodes = [
            ("Memory Retrieval", "memory_retrieval_node"),
            ("Planner", "planner_node"),
            ("Tool Execution", "tool_executor"),
            ("Reasoning", "reasoning_node"),
            ("Memory Update", "memory_update_node"),
            ("Response Node", "response_node")
        ]
        
        executed_nodes = {n["node"] for n in nodes}
        for idx, (label, node_id) in enumerate(flow_nodes):
            with flow_cols[idx]:
                is_executed = node_id in executed_nodes
                border_color = "#1DB954" if is_executed else "#282828"
                bg_color = "rgba(29, 185, 84, 0.15)" if is_executed else "rgba(255, 255, 255, 0.02)"
                text_color = "#1DB954" if is_executed else "#888888"
                
                st.markdown(
                    f"""
                    <div style="border: 2px solid {border_color}; background: {bg_color}; border-radius: 8px; padding: 10px; text-align: center; height: 100px;">
                        <b style="color: {text_color}; font-size: 0.9rem;">{label}</b>
                        <br>
                        <span style="font-size: 0.75rem; color: #888888;">{node_id}</span>
                        <br>
                        <span style="font-size: 0.8rem;">{"✅ Done" if is_executed else "💤 Idle"}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# -------------------------------------------------------------
# Tab 3: Tool Analytics
# -------------------------------------------------------------
with tab3:
    st.subheader("📈 Spotify Tool Analytics")
    
    if not st.session_state["tool_analytics"]:
        st.info("No tools invoked yet in this session. Execute query prompts that require searching, recommendation, or playlist actions to populate analytics.")
    else:
        # Calculate summary metrics
        total_invocations = sum(stats["count"] for stats in st.session_state["tool_analytics"].values())
        avg_durations = []
        for stats in st.session_state["tool_analytics"].values():
            avg_durations.extend(stats["durations"])
        avg_overall_latency = round(sum(avg_durations) / len(avg_durations), 3) if avg_durations else 0.0
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Total Tool Invocations", total_invocations)
        with m_col2:
            st.metric("Average Tool Latency", f"{avg_overall_latency}s")
            
        # Display Table
        tool_data = []
        for t_name, stats in st.session_state["tool_analytics"].items():
            success_rate = round((stats["successes"] / stats["count"]) * 100, 1)
            avg_dur = round(sum(stats["durations"]) / len(stats["durations"]), 3)
            tool_data.append({
                "Tool Name": t_name,
                "Invocations": stats["count"],
                "Success Rate": f"{success_rate}%",
                "Avg Duration": f"{avg_dur}s",
                "Last Used": stats["last_used"]
            })
            
        st.table(tool_data)

# -------------------------------------------------------------
# Tab 4: Memory Viewer
# -------------------------------------------------------------
with tab4:
    st.subheader("🧠 Long-Term Semantic Memory & Profile")
    
    active_session = st.session_state["session_id"]
    profile = memory_store.get_profile(active_session)
    is_qdrant_online = memory_store.online
    qdrant_status_str = "🟢 Qdrant Vector DB Online" if is_qdrant_online else "🟡 Offline Fallback Mode"
    st.markdown(f"**Memory Backend:** `{qdrant_status_str}`")
    
    prof_col1, prof_col2 = st.columns(2)
    with prof_col1:
        st.markdown("### 📇 User Profile Data")
        st.json(profile)
        
    with prof_col2:
        st.markdown("### 🗣️ Extracted Memories (Qdrant)")
        memories = []
        if is_qdrant_online:
            try:
                hits = memory_store.client.scroll(
                    collection_name=memory_store.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(key="session_id", match=models.MatchValue(value=active_session)),
                            models.FieldCondition(key="category", match=models.MatchValue(value="preference"))
                        ]
                    ),
                    limit=100
                )
                memories = [pt.payload for pt in hits[0]]
            except Exception as e:
                st.error(f"Error loading memories from Qdrant: {str(e)}")
        else:
            memories = [m for m in memory_store._local_memories if m["session_id"] == active_session and m["category"] == "preference"]
            
        if not memories:
            st.info("No long-term preferences stored yet. Explain your music preferences (e.g. 'I prefer deep house and ambient soundtracks') to the copilot!")
        else:
            for idx, mem in enumerate(memories):
                st.markdown(
                    f"""
                    <div style="background: rgba(255, 255, 255, 0.02); padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid #1DB954;">
                        <b>#{idx+1} Preference:</b> {mem.get('text', '')}
                        <br><span style="color: #666; font-size: 0.75rem;">Recorded at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mem.get('timestamp', 0)))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    st.markdown("---")
    if st.button("🧹 Clear Session Memory & Profile"):
        memory_store.clear(active_session)
        st.success("Session memory cleared successfully!")
        st.rerun()

# -------------------------------------------------------------
# Tab 5: System Health
# -------------------------------------------------------------
with tab5:
    st.subheader("🩺 System Status & Connection Health")
    
    health_cols = st.columns(3)
    
    with health_cols[0]:
        if memory_store.online:
            st.success("Qdrant Vector DB\n\n🟢 Connected")
            st.markdown("- **Host:** `localhost`")
            st.markdown("- **Port:** `6333`")
            st.markdown("- **Collection:** `user_memory`")
        else:
            st.warning("Qdrant Vector DB\n\n🔴 Offline (Fallback Mode)")
            st.markdown("Using in-memory dictionary. Start Qdrant Docker to enable persistent long-term memory.")
            
    with health_cols[1]:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            st.success("LLM Orchestrator\n\n🟢 Connected")
            st.markdown("- **Provider:** Groq Cloud")
            st.markdown("- **Model:** `llama-3.3-70b-versatile`")
        else:
            st.error("LLM Orchestrator\n\n🔴 Missing API Key")
            st.markdown("Set `GROQ_API_KEY` in your environment/.env file.")
            
    with health_cols[2]:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if client_id and client_secret:
            st.success("Spotify API Connection\n\n🟢 Credentials Valid")
            st.markdown("- **Auth Strategy:** Client Credentials Flow")
            st.markdown("- **Scoped Services:** recommendations, analysis, playlist, tracks")
        else:
            st.error("Spotify API Connection\n\n🔴 Credentials Missing")
            st.markdown("Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in your environment/.env file.")

# -------------------------------------------------------------
# User Input & Execution Node
# -------------------------------------------------------------
user_query = st.chat_input("Ask the Spotify Copilot (e.g. 'Generate a workout playlist with high tempo tracks')")

# Handle sidebar suggestion clicks
if selected_prompt:
    user_query = selected_prompt

if user_query:
    # 1. Show user message
    st.session_state["chat_history"].append({"role": "user", "content": user_query})
    
    # 2. Invoke LangGraph Agent with loading spinner
    with st.spinner("🎵 Copilot is planning, executing tools, and reasoning..."):
        inputs = {
            "messages": [],
            "user_query": user_query,
            "tool_calls": [],
            "tool_results": [],
            "final_response": "",
            "reasoning_steps": [],
            "session_id": st.session_state["session_id"],
            "conversation_history": [
                HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
                for m in st.session_state["chat_history"][:-1]
            ],
            "selected_tools": [],
            "metadata": {}
        }
        
        try:
            # Execute compiled graph workflow
            output_state = agent_graph.invoke(inputs)
            response_content = output_state.get("final_response", "Failed to generate response.")
            
            # Save response to history
            st.session_state["chat_history"].append({"role": "agent", "content": response_content})
            
            # Extract and update traces
            metadata = output_state.get("metadata", {})
            traces = metadata.get("execution_trace", [])
            st.session_state["latest_trace"] = {
                "user_query": user_query,
                "nodes": traces,
                "timestamp": time.time()
            }
            st.session_state["trace_history"].append(st.session_state["latest_trace"])
            
            # Extract tool traces
            tool_traces = metadata.get("tool_traces", [])
            st.session_state["latest_tool_traces"] = tool_traces
            for t in tool_traces:
                t_name = t["tool"]
                duration = t["duration"]
                success = 1.0 if t["status"] == "success" else 0.0
                
                stats = st.session_state["tool_analytics"].setdefault(t_name, {
                    "count": 0,
                    "successes": 0,
                    "durations": [],
                    "last_used": None
                })
                stats["count"] += 1
                if success:
                    stats["successes"] += 1
                stats["durations"].append(duration)
                stats["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t["start_time"]))
                
            # Rerender to display the premium output
            st.rerun()
        except Exception as e:
            st.error(f"Error executing agent workflow: {str(e)}")
            st.info("Ensure GROQ_API_KEY and SPOTIFY_CLIENT_ID credentials are correct in your .env file.")
