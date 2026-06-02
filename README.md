# 🎵 Agentic Spotify Music Copilot

An AI-powered music assistant that combines **Model Context Protocol (MCP)**, **LangGraph**, and **Google Gemini** to enable intelligent interaction with Spotify through natural language.

Unlike traditional chatbots that execute a single predefined action, this project implements an **agentic workflow** capable of understanding user intent, planning multiple actions, selecting appropriate tools, executing tasks autonomously, and generating contextual responses.

The system acts as a personal music copilot that can search for music, discover artists, analyze listening habits, generate playlists, and automate Spotify-related tasks through conversational interactions.

---

## Project Goal

The primary objective of this project is to explore and implement real-world **Agentic AI** patterns using **MCP** while building a practical Spotify assistant.

This project focuses on learning and demonstrating:

* Model Context Protocol (MCP)
* Agentic AI Workflows
* LangGraph-based Agent Orchestration
* Tool Discovery and Tool Calling
* Multi-Step Reasoning and Planning
* Context and State Management
* Spotify API Integration
* Conversational User Experiences

---

## Key Features

### 🎧 Music Discovery

* Search tracks, artists, albums, and playlists
* Discover music based on genres, moods, or artists
* Retrieve detailed track and artist information

### 🤖 Agentic Task Execution

* Interpret natural language requests
* Create execution plans dynamically
* Chain multiple tool calls automatically
* Generate contextual responses based on execution results

### 📂 Playlist Automation

* Create playlists from user prompts
* Add recommended tracks automatically
* Build mood-based or genre-based playlists
* Curate personalized music collections

### 📊 Listening Analytics

* Analyze user listening behavior
* Identify favorite artists and genres
* Generate music consumption insights
* Summarize listening trends

### 🧠 Context-Aware Conversations

* Maintain conversation context
* Remember user preferences
* Personalize future recommendations
* Support multi-turn interactions

---

## Example User Requests

```text
Search Pop tracks released after 2024
```

```text
Create a coding playlist with deep house music
```

```text
Recommend artists similar to Black Coffee
```

```text
Analyze my listening habits from the past month
```

```text
Create a sunset drive playlist and add 20 songs
```

---

## High-Level Architecture

User Interface
↓
LangGraph Agent
↓
Google Gemini
↓
MCP Client
↓
Spotify MCP Server
↓
Spotify Web API

The LangGraph agent acts as the orchestration layer responsible for reasoning, planning, tool selection, and workflow execution. MCP provides a standardized communication layer between the agent and Spotify tools, enabling dynamic discovery and execution of available capabilities.

---

## Technology Stack

| Component              | Technology     |
| ---------------------- | -------------- |
| Frontend               | Streamlit      |
| Agent Framework        | LangGraph      |
| LLM                    | Google Gemini  |
| MCP Framework          | MCP Python SDK |
| Music Platform         | Spotify API    |
| Configuration          | Pydantic       |
| Environment Management | UV             |
| Logging                | Loguru         |
| Testing                | Pytest         |

---

## Learning Outcomes

This project is designed to provide hands-on experience with:

* Building Agentic AI systems
* Designing multi-step workflows
* Implementing MCP clients and tool integration
* Managing conversational state
* Creating production-style AI architectures
* Integrating LLMs with external systems

The final result is a practical demonstration of how modern AI agents can autonomously interact with external platforms through standardized tool interfaces while maintaining context and delivering meaningful outcomes.
