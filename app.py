import streamlit as st
import os
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from src.agent.graph import agent_graph

# -------------------------------------------------------------
# Premium Spotify-Style UI Config & Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="Spotify Agentic Copilot",
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
    h1, h2, h3, h4 {
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

# Sidebar options
st.sidebar.title("🎵 Spotify Copilot")
st.sidebar.markdown("### Agent Settings")
model_selection = st.sidebar.selectbox("LLM Orchestrator", ["llama-3.3-70b-versatile (Groq)"])
session_input = st.sidebar.text_input("Session ID", value=st.session_state["session_id"])

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
# Main Chat Layout
# -------------------------------------------------------------
st.title("🎵 Spotify Agentic Music Copilot")
st.markdown("##### *A fully decoupled, LangGraph-powered AI music curator that plans, executes, and reasons over Spotify data.*")
st.markdown("---")

# Message history feed container
chat_container = st.container()

with chat_container:
    for message in st.session_state["chat_history"]:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-bubble user-bubble"><b>You:</b><br>{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble agent-bubble">{message["content"]}</div>', unsafe_allow_html=True)

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
    st.markdown(f'<div class="chat-bubble user-bubble"><b>You:</b><br>{user_query}</div>', unsafe_allow_html=True)
    
    # 2. Invoke LangGraph Agent with loading spinner
    with st.spinner("🎵 Copilot is planning, executing tools, and reasoning..."):
        # Build initial AgentState input
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
            
            # Rerender to display the premium output
            st.rerun()
        except Exception as e:
            st.error(f"Error executing agent workflow: {str(e)}")
            st.info("Ensure GROQ_API_KEY and SPOTIFY_CLIENT_ID credentials are correct in your .env file.")
