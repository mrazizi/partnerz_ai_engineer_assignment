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
    .cart-item {
        background-color: #fff3e0;
        color: #333333;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
        border-left: 4px solid #ff9800;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'cart_id' not in st.session_state:
        st.session_state.cart_id = None
    
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


def get_cart_contents():
    """Get cart contents if cart exists."""
    if not st.session_state.cart_id:
        return None
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/cart/{st.session_state.cart_id}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


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
                    st.markdown(f'<div class="bot-message"><strong>Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)


def display_product_search():
    """Display product search interface."""
    st.markdown("### 🔍 Quick Product Search")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "Search for products:",
            placeholder="e.g., red shirt, running shoes, etc.",
            key="search_input"
        )
    
    with col2:
        search_button = st.button("Search", type="primary")
    
    if search_button and search_query:
        with st.spinner("Searching products..."):
            results = search_products(search_query)
            
            if "error" in results:
                st.error(f"Search failed: {results['error']}")
            else:
                products = results.get("products", [])
                if products:
                    st.success(f"Found {len(products)} products:")
                    
                    # Display products in a grid
                    for i in range(0, len(products), 2):
                        cols = st.columns(2)
                        for j, col in enumerate(cols):
                            if i + j < len(products):
                                product = products[i + j]
                                with col:
                                    with st.container():
                                        st.markdown(f'<div class="product-card">', unsafe_allow_html=True)
                                        st.markdown(f"**{product['title']}**")
                                        st.markdown(f"Price: ${product['price']:.2f}")
                                        if product['description']:
                                            st.markdown(f"{product['description'][:100]}...")
                                        
                                        # Show availability
                                        if True:  # Default to available since we removed the field
                                            st.markdown('<span class="status-indicator status-connected">In Stock</span>', unsafe_allow_html=True)
                                        else:
                                            st.markdown('<span class="status-indicator status-error">Out of Stock</span>', unsafe_allow_html=True)
                                        
                                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("No products found for your search.")


def display_cart_summary():
    """Display cart summary in sidebar."""
    cart_data = get_cart_contents()
    
    if cart_data and cart_data.get("cart"):
        cart = cart_data["cart"]
        cart_lines = cart.get("lines", {}).get("edges", [])
        
        if cart_lines:
            st.markdown("### 🛒 Your Cart")
            
            total = 0.0
            for line in cart_lines:
                node = line["node"]
                merchandise = node["merchandise"]
                product_title = merchandise["product"]["title"]
                variant_title = merchandise["title"]
                quantity = node["quantity"]
                price = float(merchandise["price"]["amount"])
                
                line_total = price * quantity
                total += line_total
                
                st.markdown(f'''
                <div class="cart-item">
                    <strong>{product_title}</strong><br>
                    {variant_title}<br>
                    Qty: {quantity} × ${price:.2f} = ${line_total:.2f}
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown(f"**Total: ${total:.2f}**")
            
            if st.button("🗑️ Clear Cart"):
                if clear_conversation():
                    st.rerun()
        else:
            st.markdown("### 🛒 Your Cart")
            st.write("Your cart is empty")
    else:
        st.markdown("### 🛒 Your Cart")
        st.write("Your cart is empty")


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
        
        # Display cart summary
        if backend_connected:
            display_cart_summary()
        
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
    
    # Chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
    
    with col2:
        # Product search interface
        display_product_search()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        Shopify Shopping Assistant | Powered by OpenAI GPT-4 and Shopify Storefront API
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
