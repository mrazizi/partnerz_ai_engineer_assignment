"""Streamlit frontend for Shopify Conversational Agent."""
import streamlit as st
import requests
import json
import uuid
from typing import Dict, Any, List
import time

# Page configuration
st.set_page_config(
    page_title="Shopify Shopping Assistant",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
BACKEND_URL = "http://backend:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #96c93d;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #2196f3;
        color: white;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        margin-left: 2rem;
        border-left: 4px solid #1976d2;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .bot-message {
        background-color: #f5f5f5;
        color: #333333;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        margin-right: 2rem;
        border-left: 4px solid #4caf50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .product-card {
        background-color: #ffffff;
        color: #333333;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .status-indicator {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-connected {
        background-color: #c8e6c9;
        color: #2e7d32;
    }
    .status-error {
        background-color: #ffcdd2;
        color: #c62828;
    }

    .message-text {
        color: inherit;
        font-weight: 500;
        line-height: 1.5;
    }
    .product-title {
        color: #1976d2;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .product-price {
        color: #2e7d32;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .product-description {
        color: #666666;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    .bot-message a {
        color: #1976d2;
        text-decoration: underline;
        font-weight: 500;
    }
    .bot-message a:hover {
        color: #1565c0;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    

    
    if 'backend_connected' not in st.session_state:
        st.session_state.backend_connected = False


def check_backend_connection():
    """Check if backend is accessible."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            st.session_state.backend_connected = True
            return True
        else:
            st.session_state.backend_connected = False
            return False
    except Exception as e:
        st.session_state.backend_connected = False
        return False


def send_chat_message(message: str) -> str:
    """Send chat message to backend and get response."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result["response"]
    except Exception as e:
        return f"Error: Could not process your message. {str(e)}"


def get_conversation_history():
    """Get conversation history from backend."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/conversation/{st.session_state.session_id}",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("conversation_history", [])
        return []
    except Exception:
        return []


def clear_conversation():
    """Clear conversation history."""
    try:
        requests.delete(
            f"{BACKEND_URL}/conversation/{st.session_state.session_id}",
            timeout=10
        )
        st.session_state.conversation_history = []
        st.session_state.session_id = str(uuid.uuid4())
        return True
    except Exception:
        return False


def search_products(query: str, limit: int = 10):
    """Search for products."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/search",
            json={"query": query, "limit": limit},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}





def display_chat_history():
    """Display chat conversation history."""
    if st.session_state.conversation_history:
        st.markdown("### 💬 Conversation")
        
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.conversation_history:
                if message["role"] == "user":
                    st.markdown(f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    # Convert markdown links to HTML for proper rendering
                    content = message["content"]
                    # Convert markdown links [text](url) to HTML links
                    import re
                    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', content)
                    st.markdown(f'<div class="bot-message"><strong>Assistant:</strong> {content}</div>', unsafe_allow_html=True)





def main():
    """Main application function."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🛍️ Shopify Shopping Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("System Status")
        
        # Check backend connection
        backend_connected = check_backend_connection()
        if backend_connected:
            st.markdown('<span class="status-indicator status-connected">✅ Backend Connected</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-error">❌ Backend Disconnected</span>', unsafe_allow_html=True)
            st.warning("Please ensure the backend server is running and accessible")
        
        st.markdown("---")
        
        # Session management
        st.header("Session Management")
        st.write(f"Session ID: `{st.session_state.session_id[:8]}...`")
        
        if st.button("🔄 New Conversation"):
            if clear_conversation():
                st.rerun()
        
        # Quick actions
        st.header("Quick Actions")
        example_queries = [
            "I want an earrings",
            "What Sandals do you have?",
            "Show me shirts",
            "What's in my cart?",
            "Remove last item"
        ]
        
        for query in example_queries:
            if st.button(f"💬 {query}", key=f"quick_{query}"):
                if backend_connected:
                    with st.spinner("Processing..."):
                        response = send_chat_message(query)
                        st.session_state.conversation_history.append({"role": "user", "content": query})
                        st.session_state.conversation_history.append({"role": "assistant", "content": response})
                    st.rerun()
    
    # Main content
    if not backend_connected:
        st.error("⚠️ Backend server is not accessible. Please start the backend server and refresh this page.")
        st.code("cd task2/backend && python run.py", language="bash")
        return
    
    # Chat interface - Full width
    # Display conversation history
    display_chat_history()
    
    # Chat input
    st.markdown("### 💭 Chat with Assistant")
    
    # Create a form for better UX
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your message:",
            height=100,
            placeholder="Ask me about products, sizes, colors, or cart management...",
            key="user_message"
        )
        
        col_send, col_clear = st.columns([1, 1])
        
        with col_send:
            send_button = st.form_submit_button("Send Message", type="primary")
        
        with col_clear:
            clear_button = st.form_submit_button("Clear Chat")
    
    # Process user input
    if send_button and user_input.strip():
        with st.spinner("Thinking..."):
            response = send_chat_message(user_input.strip())
            
            # Add to conversation history
            st.session_state.conversation_history.append({"role": "user", "content": user_input.strip()})
            st.session_state.conversation_history.append({"role": "assistant", "content": response})
        
        st.rerun()
    
    if clear_button:
        if clear_conversation():
            st.rerun()
    
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        Shopify Shopping Assistant | Powered by OpenAI GPT-4 and Shopify Storefront API
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
