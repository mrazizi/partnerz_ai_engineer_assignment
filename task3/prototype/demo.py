#!/usr/bin/env python3
"""
Demo script to showcase the recommendation system with a smaller dataset.
This creates a minimal working example for testing.
"""
import json
import os
import sys
import random
from typing import Dict, Any, List

# Add backend to path
sys.path.append('backend')

from backend.embedding_service import EmbeddingService
from backend.recommendation_engine import RecommendationEngine

def create_demo_products() -> List[Dict[str, Any]]:
    """Create a small set of demo products."""
    demo_products = [
        {
            "id": "demo_001",
            "title": "Blue Cotton T-Shirt",
            "description": "Comfortable cotton t-shirt in blue color. Perfect for casual wear.",
            "handle": "blue-cotton-tshirt",
            "price": 29.99,
            "currency": "USD",
            "images": "https://example.com/blue-tshirt.jpg",
            "variants": []
        },
        {
            "id": "demo_002", 
            "title": "Red Cotton T-Shirt",
            "description": "Comfortable cotton t-shirt in red color. Perfect for casual wear.",
            "handle": "red-cotton-tshirt",
            "price": 29.99,
            "currency": "USD",
            "images": "https://example.com/red-tshirt.jpg",
            "variants": []
        },
        {
            "id": "demo_003",
            "title": "Blue Jeans",
            "description": "Classic blue denim jeans. Durable and comfortable for everyday wear.",
            "handle": "blue-jeans",
            "price": 79.99,
            "currency": "USD", 
            "images": "https://example.com/blue-jeans.jpg",
            "variants": []
        },
        {
            "id": "demo_004",
            "title": "Black Jeans",
            "description": "Stylish black denim jeans. Perfect for both casual and semi-formal occasions.",
            "handle": "black-jeans",
            "price": 89.99,
            "currency": "USD",
            "images": "https://example.com/black-jeans.jpg",
            "variants": []
        },
        {
            "id": "demo_005",
            "title": "Leather Wallet",
            "description": "Premium leather wallet with multiple card slots and cash compartments.",
            "handle": "leather-wallet",
            "price": 49.99,
            "currency": "USD",
            "images": "https://example.com/leather-wallet.jpg",
            "variants": []
        },
        {
            "id": "demo_006",
            "title": "Canvas Bag",
            "description": "Eco-friendly canvas tote bag. Great for shopping and daily use.",
            "handle": "canvas-bag",
            "price": 24.99,
            "currency": "USD",
            "images": "https://example.com/canvas-bag.jpg",
            "variants": []
        },
        {
            "id": "demo_007",
            "title": "White Sneakers",
            "description": "Classic white sneakers. Comfortable and versatile for any outfit.",
            "handle": "white-sneakers",
            "price": 89.99,
            "currency": "USD",
            "images": "https://example.com/white-sneakers.jpg",
            "variants": []
        },
        {
            "id": "demo_008",
            "title": "Black Sneakers",
            "description": "Stylish black sneakers. Perfect for sports and casual wear.",
            "handle": "black-sneakers",
            "price": 94.99,
            "currency": "USD",
            "images": "https://example.com/black-sneakers.jpg",
            "variants": []
        }
    ]
    
    return demo_products

def create_demo_interactions(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create realistic demo interactions."""
    interactions = []
    product_ids = [p["id"] for p in products]
    
    # Define user purchase patterns (realistic combinations)
    purchase_patterns = [
        ["demo_001", "demo_003"],  # Blue t-shirt + blue jeans
        ["demo_001", "demo_003", "demo_007"],  # Blue t-shirt + blue jeans + white sneakers
        ["demo_002", "demo_004"],  # Red t-shirt + black jeans  
        ["demo_002", "demo_004", "demo_008"],  # Red t-shirt + black jeans + black sneakers
        ["demo_003", "demo_005"],  # Blue jeans + wallet
        ["demo_004", "demo_005"],  # Black jeans + wallet
        ["demo_006", "demo_007"],  # Canvas bag + white sneakers
        ["demo_006", "demo_008"],  # Canvas bag + black sneakers
        ["demo_001", "demo_005"],  # T-shirt + wallet
        ["demo_002", "demo_005"],  # T-shirt + wallet
        ["demo_007", "demo_005"],  # Sneakers + wallet
        ["demo_008", "demo_005"],  # Sneakers + wallet
    ]
    
    # Generate interactions based on patterns
    for user_id in range(100):  # 100 demo users
        # Some users follow patterns, others are random
        if random.random() < 0.7:  # 70% follow patterns
            pattern = random.choice(purchase_patterns)
            user_products = pattern
        else:  # 30% random
            num_products = random.randint(1, 3)
            user_products = random.sample(product_ids, num_products)
        
        for product_id in user_products:
            interaction = {
                "user_id": f"demo_user_{user_id}",
                "product_id": product_id,
                "interaction_type": random.choice(["view", "add_to_cart", "purchase"]),
                "timestamp": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            }
            interactions.append(interaction)
    
    return interactions

def run_demo():
    """Run the complete demo pipeline."""
    print("🚀 Starting Recommendation System Demo")
    print("="*50)
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Step 1: Create demo products
    print("📦 Creating demo products...")
    products = create_demo_products()
    with open("data/products.json", "w") as f:
        json.dump(products, f, indent=2)
    print(f"✅ Created {len(products)} demo products")
    
    # Step 2: Generate embeddings
    print("\n🔍 Generating embeddings...")
    embedding_service = EmbeddingService()
    result = embedding_service.process_products(products)
    print(f"✅ Processed embeddings: {result}")
    
    # Step 3: Create demo interactions
    print("\n👥 Creating demo interactions...")
    interactions = create_demo_interactions(products)
    with open("data/interactions.json", "w") as f:
        json.dump(interactions, f, indent=2)
    print(f"✅ Created {len(interactions)} demo interactions")
    
    # Step 4: Create co-occurrence and lift scores (simplified)
    print("\n📊 Creating co-occurrence matrix...")
    from backend.data_fetcher import DataFetcher
    fetcher = DataFetcher()
    co_occurrence = fetcher.create_co_occurrence_matrix(interactions)
    lift_scores = fetcher.calculate_lift_scores(co_occurrence, interactions)
    print(f"✅ Created co-occurrence matrix and lift scores")
    
    # Step 5: Generate recommendations
    print("\n🎯 Generating recommendations...")
    engine = RecommendationEngine()
    recommendations = engine.generate_all_recommendations()
    print(f"✅ Generated recommendations: {recommendations}")
    
    # Step 6: Show sample recommendations
    print("\n" + "="*50)
    print("📋 SAMPLE RECOMMENDATIONS")
    print("="*50)
    
    # Show recommendations for first product
    sample_product = products[0]
    rec_result = engine.generate_recommendations(sample_product["id"])
    
    print(f"\n🎯 Target Product: {sample_product['title']}")
    print(f"   Price: {sample_product['currency']} {sample_product['price']}")
    print(f"   Description: {sample_product['description'][:100]}...")
    
    print(f"\n💡 Top Recommendations:")
    for i, rec in enumerate(rec_result.get("recommendations", [])[:3], 1):
        product_info = rec["product_info"]
        scores = rec["score_breakdown"]
        
        print(f"\n   {i}. {product_info['title']}")
        print(f"      Price: {product_info['currency']} {product_info['price']}")
        print(f"      Final Score: {rec['final_score']:.4f}")
        print(f"      Collaborative: {scores['collaborative_score']:.4f} ({scores['collaborative_interactions']} shared users)")
        print(f"      Content Similarity: {scores['content_score']:.4f}")
        print(f"      Enrichment: {scores['enrichment_score']:.4f}")
    
    print(f"\n" + "="*50)
    print("🎉 Demo completed! Check the data/ directory for generated files.")
    print("🚀 Next steps:")
    print("   1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:latest")
    print("   2. Run full pipeline: python run_pipeline.py")
    print("   3. Start backend: cd backend && python main.py")
    print("   4. Start frontend: cd frontend && streamlit run app.py")

if __name__ == "__main__":
    run_demo()
