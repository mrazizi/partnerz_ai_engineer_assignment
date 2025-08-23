import streamlit as st
import requests
import json
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="Intercom Help Center RAG",
    page_icon="🤖",
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
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
    }
    .source-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .answer-box {
        background-color: #e8f5e8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

def check_backend_connection():
    """Check if backend is accessible."""
    try:
        print(f"Attempting to connect to {BACKEND_URL}/health")
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Connection error: {e}")
        return False

def query_rag_system(question: str) -> Dict[str, Any]:
    """Query the RAG system."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"question": question},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        return result
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def ingest_data():
    """Trigger data ingestion."""
    try:
        response = requests.post(f"{BACKEND_URL}/ingest", timeout=300)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Intercom Help Center RAG System</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("System Status")
        
        # Check backend connection
        backend_connected = check_backend_connection()
        if backend_connected:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Disconnected")
            st.warning("Please ensure the backend server is running and accessible")

        
        # Data ingestion
        st.header("Data Management")
        if st.button("🔄 Ingest Articles Data", help="Load and index articles from JSON file"):
            if backend_connected:
                with st.spinner("Ingesting data... This may take a few minutes."):
                    result = ingest_data()
                    if result.get("status") == "success":
                        st.success("✅ Data ingestion completed!")
                    else:
                        st.error(f"❌ Ingestion failed: {result.get('error', 'Unknown error')}")
            else:
                st.error("Backend not connected")
    
    # Main content
    if not backend_connected:
        st.error("⚠️ Backend server is not accessible. Please start the backend server and refresh this page.")
        st.code("cd backend && python main.py", language="bash")
        return
    
    # Query interface
    st.header("Ask Questions About Intercom")
    
    # Example queries
    st.subheader("Try These Example Queries:")
    example_queries = [
        "How do I reset my password?",
        "What integrations does Intercom support?",
        "Can I change my billing cycle mid-subscription?",
        "How can I customize my widget?"
    ]
    
    cols = st.columns(2)
    for i, query in enumerate(example_queries):
        col = cols[i % 2]
        if col.button(f"📝 {query}", key=f"example_{i}"):
            st.session_state.query_input = query
    
    # Query input
    query = st.text_area(
        "Enter your question:",
        value=st.session_state.get("query_input", ""),
        height=100,
        placeholder="Type your question about Intercom here...",
        key="query_text"
    )
    
    # Submit button
    if st.button("🔍 Ask Question", type="primary"):
        if query.strip():
            with st.spinner("Searching for answer..."):
                result = query_rag_system(query.strip())
                
                if "error" in result and result["error"] is not None:
                    st.markdown(f'<div class="error-box">❌ {result["error"]}</div>', unsafe_allow_html=True)
                else:
                    # Get answer from result
                    answer = result.get("answer")
                    
                    # Debug: Print the answer value and type
                    print(f"Answer value: '{answer}' (type: {type(answer)})")
                    print(f"Answer is truthy: {bool(answer)}")
                    
                    # Display the answer directly
                    if answer:
                        st.write("### 💡 Answer")
                        st.write(answer)
                        
                        # Display sources with toggle
                        if result.get("sources"):
                            with st.expander("📚 Sources", expanded=False):
                                for i, source in enumerate(result["sources"], 1):
                                    st.write(f"**Source {i}:**")
                                    st.write(f"Title: {source.get('title', 'No title')}")
                                    st.write(f"URL: {source.get('url', 'No URL')}")
                                    st.write(f"Content: {source.get('content_snippet', 'No content')[:100]}...")
                                    st.write("---")
                    else:
                        st.error("❌ No answer received from the backend")
                        st.write("Raw result:")
                        st.json(result)
        else:
            st.warning("Please enter a question.")
    
    # Clear query button
    if st.button("🗑️ Clear"):
        st.session_state.query_input = ""
        st.experimental_rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        Intercom Help Center RAG System | Powered by LangChain, Qdrant, and OpenAI
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

