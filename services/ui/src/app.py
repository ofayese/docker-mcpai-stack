"""
Streamlit UI for Docker MCP Stack
Modern interface for interacting with LLMs and MCP services
"""

import streamlit as st
import requests
import json
import os
import plotly.graph_objects as go
import pandas as pd
import time
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
    """Send a chat message to the API and get a response"""
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        # Send the request via MCP API
        url = f"{MCP_API_URL}/v1/chat/completions"
        response = requests.post(
            url,
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"
    return "No response received"

def get_prometheus_metrics() -> Dict[str, Any]:
    """Fetch API request counts by endpoint from Prometheus."""
    try:
        resp = requests.get(
            f"http://prometheus:9090/api/v1/query",
            params={"query": "sum(mcp_api_requests_total) by (endpoint)"},
            timeout=5
        )
        results = resp.json().get("data", {}).get("result", [])
        endpoints = [item["metric"].get("endpoint", "") for item in results]
        values = [float(item["value"][1]) for item in results]
        return {"endpoint": endpoints, "requests": values}
    except Exception:
        return {}

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

    # Fetch metrics from MCP API
    try:
        metrics_resp = requests.get(f"{MCP_API_URL}/v1/metrics/metrics", timeout=5)
        if metrics_resp.status_code == 200:
            metrics_data = metrics_resp.json()
            st.metric("API Requests", metrics_data.get("requests_total", 0))
            st.metric("Active Requests", metrics_data.get("active_requests", 0))
            st.metric("Model Inferences", metrics_data.get("model_inferences_total", 0))
            sysinfo = metrics_data.get("system_info", {})
            st.caption(f"Python: {sysinfo.get('python_version', 'N/A')} | Platform: {sysinfo.get('platform', 'N/A')}")
        else:
            st.warning("Could not fetch metrics from MCP API.")
    except Exception as e:
        st.warning(f"Metrics unavailable: {e}")

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

# After system info and quick links:
st.subheader("📈 Metrics Dashboard")
metrics = get_prometheus_metrics()
if metrics.get("endpoint"):
    df = pd.DataFrame(metrics)
    fig = go.Figure([go.Bar(x=df["endpoint"], y=df["requests"])])
    fig.update_layout(title="API Requests by Endpoint", xaxis_title="Endpoint", yaxis_title="Requests Total")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Metrics data not available or no requests recorded yet.")

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ using Docker, Streamlit, and the Model Context Protocol",
    help="Docker MCP Stack - Cross-platform GenAI development environment"
)
