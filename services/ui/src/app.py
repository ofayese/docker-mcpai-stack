"""
Streamlit UI for Docker MCP Stack
Modern interface for interacting with LLMs and MCP services
"""

import streamlit as st
import requests
import json
import os
from typing import Dict, Any

# Configuration
MODEL_API_URL = os.getenv("MODEL_API_URL", "http://model-runner:8080/v1")
MCP_API_URL = os.getenv("MCP_API_URL", "http://mcp-api:4000")

st.set_page_config(
    page_title="Docker MCP Stack",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
    }
    .status-healthy {
        color: #28a745;
        font-weight: bold;
    }
    .status-unhealthy {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def check_service_health(url: str, service_name: str) -> bool:
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_available_models() -> list:
    """Get list of available models"""
    try:
        response = requests.get(f"{MODEL_API_URL}/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
    except:
        pass
    return []

def send_chat_message(message: str, model: str) -> str:
    """Send chat message to model"""
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 500,
            "temperature": 0.7
        }
        response = requests.post(
            f"{MODEL_API_URL}/chat/completions",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"
    return "No response received"

# Main header
st.markdown('<div class="main-header">🤖 Docker MCP Stack</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Service status
    st.subheader("Service Status")
    
    services = [
        ("Model Runner", MODEL_API_URL),
        ("MCP API", MCP_API_URL),
        ("Vector DB", "http://qdrant:6333")
    ]
    
    for service_name, service_url in services:
        is_healthy = check_service_health(service_url, service_name)
        status_class = "status-healthy" if is_healthy else "status-unhealthy"
        status_text = "🟢 Healthy" if is_healthy else "🔴 Unhealthy"
        st.markdown(f"{service_name}: <span class='{status_class}'>{status_text}</span>", 
                   unsafe_allow_html=True)
    
    st.divider()
    
    # Model selection
    st.subheader("Model Selection")
    models = get_available_models()
    
    if models:
        model_names = [model["id"] for model in models]
        selected_model = st.selectbox("Choose Model", model_names)
    else:
        st.error("No models available")
        selected_model = None
    
    st.divider()
    
    # Settings
    st.subheader("Chat Settings")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("Max Tokens", 50, 1000, 500, 50)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Chat Interface")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        if selected_model:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = send_chat_message(prompt, selected_model)
                st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            st.error("Please select a model first")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

with col2:
    st.header("📊 System Info")
    
    # System metrics (placeholder)
    st.metric("Active Models", len(models) if models else 0)
    st.metric("Chat Messages", len(st.session_state.get("messages", [])))
    
    st.subheader("🔗 Quick Links")
    st.markdown("""
    - [Prometheus](http://localhost:9090) - Metrics
    - [Grafana](http://localhost:3000) - Dashboards  
    - [Qdrant](http://localhost:6333/dashboard) - Vector DB
    - [Model API](http://localhost:8080) - Models
    """)
    
    st.subheader("📚 Documentation")
    st.markdown("""
    - [MCP Protocol](https://github.com/microsoft/mcp)
    - [Model Runner](https://github.com/docker/model-runner)
    - [Docker Compose](https://docs.docker.com/compose/)
    """)

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ using Docker, Streamlit, and the Model Context Protocol",
    help="Docker MCP Stack - Cross-platform GenAI development environment"
)
