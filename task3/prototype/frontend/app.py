"""Streamlit frontend for the recommendation system prototype."""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Product Recommendation System",
    page_icon="🛍️",
    layout="wide"
)

@st.cache_data
def get_products() -> List[Dict[str, Any]]:
    """Get all products from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/products")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching products: {e}")
        return []

@st.cache_data
def get_recommendations(product_id: str) -> Dict[str, Any]:
    """Get recommendations for a specific product."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/recommendations",
            json={"product_id": product_id},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching recommendations: {e}")
        return {}

@st.cache_data
def get_stats() -> Dict[str, Any]:
    """Get system statistics."""
    try:
        response = requests.get(f"{BACKEND_URL}/stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {}

def display_product_card(product: Dict[str, Any], show_full_description: bool = False):
    """Display a product card."""
    with st.container():
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Display product image if available
            if product.get("images"):
                st.image(product["images"], width=150, use_column_width=True)
            else:
                st.write("📷 No image")
        
        with col2:
            st.subheader(product["title"])
            st.write(f"**Price:** {product['currency']} {product['price']:.2f}")
            st.write(f"**Product ID:** {product['id']}")
            
            # Description
            description = product.get("description", "No description available")
            if show_full_description or len(description) <= 200:
                st.write(f"**Description:** {description}")
            else:
                st.write(f"**Description:** {description[:200]}...")

def display_score_breakdown(score_breakdown: Dict[str, float]):
    """Display score breakdown with visualizations."""
    st.subheader("Score Breakdown")
    
    # Create score breakdown chart
    scores = {
        "Collaborative (Lift)": score_breakdown["collaborative_score"],
        "Content Similarity": score_breakdown["content_score"],
        "Enrichment": score_breakdown["enrichment_score"]
    }
    
    # Create a bar chart
    fig = px.bar(
        x=list(scores.keys()),
        y=list(scores.values()),
        title="Score Components",
        labels={"x": "Score Type", "y": "Score Value"},
        color=list(scores.values()),
        color_continuous_scale="viridis"
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display numerical values
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Collaborative Score", f"{score_breakdown['collaborative_score']:.4f}")
    
    with col2:
        st.metric("Content Score", f"{score_breakdown['content_score']:.4f}")
    
    with col3:
        st.metric("Enrichment Score", f"{score_breakdown['enrichment_score']:.4f}")
    
    with col4:
        st.metric("Shared Interactions", int(score_breakdown['collaborative_interactions']))

def display_recommendations(recommendations: Dict[str, Any]):
    """Display recommendations with detailed breakdown."""
    target_product = recommendations["target_product"]
    rec_list = recommendations["recommendations"]
    
    st.header("🎯 Target Product")
    display_product_card(target_product, show_full_description=True)
    
    st.header("💡 Recommended Products")
    
    if not rec_list:
        st.warning("No recommendations found for this product.")
        return
    
    # Summary statistics
    st.subheader("📊 Recommendation Summary")
    debug_info = recommendations.get("debug_info", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Recommendations", len(rec_list))
    with col2:
        st.metric("Collaborative Candidates", debug_info.get("collaborative_candidates_count", 0))
    with col3:
        st.metric("Content Candidates", debug_info.get("content_candidates_count", 0))
    with col4:
        st.metric("Enrichment Candidates", debug_info.get("enrichment_candidates_count", 0))
    
    # Display each recommendation
    for i, rec in enumerate(rec_list, 1):
        st.subheader(f"Recommendation #{i}")
        
        # Product info
        product_info = rec["product_info"]
        score_breakdown = rec["score_breakdown"]
        final_score = rec["final_score"]
        
        # Two column layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_product_card(product_info)
            st.write(f"**Final Score:** {final_score:.4f}")
        
        with col2:
            display_score_breakdown(score_breakdown)
        
        st.divider()

def main():
    """Main application."""
    st.title("🛍️ Product Recommendation System Prototype")
    st.markdown("*Hybrid recommendation system combining collaborative filtering and content-based approaches*")
    
    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Product Recommendations", "System Statistics"])
    
    if page == "Product Recommendations":
        st.header("Product Recommendations")
        
        # Get products
        products = get_products()
        
        if not products:
            st.error("No products available. Please run the data fetcher first.")
            return
        
        # Product selection
        product_options = {f"{p['title']} (ID: {p['id']})": p['id'] for p in products[:50]}  # Show first 50 for demo
        
        selected_product_display = st.selectbox("Select a product:", list(product_options.keys()))
        selected_product_id = product_options[selected_product_display]
        
        if st.button("Get Recommendations", type="primary"):
            with st.spinner("Generating recommendations..."):
                recommendations = get_recommendations(selected_product_id)
                
                if recommendations:
                    display_recommendations(recommendations)
                else:
                    st.error("Failed to get recommendations.")
    
    elif page == "System Statistics":
        st.header("📈 System Statistics")
        
        stats = get_stats()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Products", stats.get("products_count", 0))
            
            with col2:
                st.metric("Interactions", stats.get("interactions_count", 0))
            
            with col3:
                st.metric("Recommendations", stats.get("recommendations_count", 0))
            
            with col4:
                qdrant_status = stats.get("qdrant", {}).get("status", "unknown")
                st.metric("Qdrant Status", qdrant_status)
            
            # Qdrant details
            st.subheader("Qdrant Vector Database")
            qdrant_info = stats.get("qdrant", {})
            
            if qdrant_info.get("status") == "connected":
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Collection Name", qdrant_info.get("collection_name", "N/A"))
                    st.metric("Points Count", qdrant_info.get("points_count", 0))
                
                with col2:
                    st.metric("Vectors Count", qdrant_info.get("vectors_count", 0))
            else:
                st.error(f"Qdrant connection error: {qdrant_info.get('error', 'Unknown error')}")
        
        else:
            st.error("Failed to get system statistics.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit, FastAPI, Qdrant, and OpenAI*")

if __name__ == "__main__":
    main()
