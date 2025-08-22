#!/usr/bin/env python3
"""
Minimal Recommendation Engine Prototype
======================================

This prototype demonstrates a basic recommendation system that can be used
to generate "Customers also bought/viewed" recommendations for product pages.

Features:
- Content-based filtering using product attributes
- Simple collaborative filtering based on purchase patterns
- Hybrid recommendations combining multiple approaches
- Real-time API for serving recommendations
"""

import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Product data model."""
    id: str
    title: str
    category: str
    price: float
    brand: str
    tags: List[str]
    description: str


@dataclass
class UserInteraction:
    """User interaction data model."""
    user_id: str
    product_id: str
    interaction_type: str  # 'view', 'purchase', 'cart_add'
    timestamp: datetime
    session_id: str


@dataclass
class Recommendation:
    """Recommendation result."""
    product_id: str
    score: float
    reason: str
    algorithm: str


class RecommendationEngine:
    """Main recommendation engine implementation."""
    
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.interactions: List[UserInteraction] = []
        self.product_similarity_matrix = None
        self.tfidf_vectorizer = None
        self.scaler = StandardScaler()
        self.interaction_matrix = None
        
    def load_sample_data(self):
        """Load sample product and interaction data."""
        
        # Sample products (simulating Shopify store data)
        sample_products = [
            Product("1", "Classic White T-Shirt", "Clothing", 29.99, "BasicWear", ["cotton", "casual", "white"], "Comfortable cotton t-shirt"),
            Product("2", "Blue Denim Jeans", "Clothing", 79.99, "DenimCo", ["denim", "casual", "blue"], "Classic blue jeans"),
            Product("3", "Red Hoodie", "Clothing", 59.99, "BasicWear", ["cotton", "casual", "red"], "Warm cotton hoodie"),
            Product("4", "Black Sneakers", "Footwear", 89.99, "ShoeCorp", ["athletic", "black", "casual"], "Comfortable athletic shoes"),
            Product("5", "White Sneakers", "Footwear", 94.99, "ShoeCorp", ["athletic", "white", "casual"], "Premium white sneakers"),
            Product("6", "Leather Jacket", "Clothing", 199.99, "LeatherLux", ["leather", "jacket", "black"], "Premium leather jacket"),
            Product("7", "Cotton Socks", "Accessories", 12.99, "BasicWear", ["cotton", "white", "basic"], "Pack of cotton socks"),
            Product("8", "Baseball Cap", "Accessories", 24.99, "CapCo", ["hat", "cotton", "adjustable"], "Adjustable baseball cap"),
            Product("9", "Backpack", "Accessories", 49.99, "BagBrand", ["travel", "durable", "black"], "Durable travel backpack"),
            Product("10", "Running Shorts", "Clothing", 34.99, "ActiveWear", ["athletic", "shorts", "breathable"], "Lightweight running shorts"),
        ]
        
        for product in sample_products:
            self.products[product.id] = product
        
        # Sample user interactions
        sample_interactions = [
            # User 1 interactions
            UserInteraction("user1", "1", "view", datetime.now() - timedelta(days=1), "session1"),
            UserInteraction("user1", "2", "view", datetime.now() - timedelta(days=1), "session1"),
            UserInteraction("user1", "1", "purchase", datetime.now() - timedelta(days=1), "session1"),
            UserInteraction("user1", "7", "purchase", datetime.now() - timedelta(days=1), "session1"),
            
            # User 2 interactions
            UserInteraction("user2", "1", "view", datetime.now() - timedelta(hours=12), "session2"),
            UserInteraction("user2", "7", "view", datetime.now() - timedelta(hours=12), "session2"),
            UserInteraction("user2", "8", "view", datetime.now() - timedelta(hours=12), "session2"),
            UserInteraction("user2", "1", "purchase", datetime.now() - timedelta(hours=12), "session2"),
            UserInteraction("user2", "8", "purchase", datetime.now() - timedelta(hours=12), "session2"),
            
            # User 3 interactions
            UserInteraction("user3", "4", "view", datetime.now() - timedelta(hours=6), "session3"),
            UserInteraction("user3", "5", "view", datetime.now() - timedelta(hours=6), "session3"),
            UserInteraction("user3", "10", "view", datetime.now() - timedelta(hours=6), "session3"),
            UserInteraction("user3", "4", "purchase", datetime.now() - timedelta(hours=6), "session3"),
            UserInteraction("user3", "10", "purchase", datetime.now() - timedelta(hours=6), "session3"),
            
            # Additional interactions for pattern building
            UserInteraction("user4", "6", "view", datetime.now() - timedelta(hours=3), "session4"),
            UserInteraction("user4", "2", "view", datetime.now() - timedelta(hours=3), "session4"),
            UserInteraction("user4", "6", "purchase", datetime.now() - timedelta(hours=3), "session4"),
            
            UserInteraction("user5", "3", "view", datetime.now() - timedelta(hours=2), "session5"),
            UserInteraction("user5", "2", "view", datetime.now() - timedelta(hours=2), "session5"),
            UserInteraction("user5", "9", "view", datetime.now() - timedelta(hours=2), "session5"),
            UserInteraction("user5", "3", "purchase", datetime.now() - timedelta(hours=2), "session5"),
            UserInteraction("user5", "9", "purchase", datetime.now() - timedelta(hours=2), "session5"),
        ]
        
        self.interactions = sample_interactions
        logger.info(f"Loaded {len(self.products)} products and {len(self.interactions)} interactions")
    
    def build_content_similarity(self):
        """Build product similarity matrix based on content features."""
        
        product_list = list(self.products.values())
        
        # Create feature vectors combining text and numerical features
        text_features = []
        numerical_features = []
        
        for product in product_list:
            # Text features: title + category + brand + tags + description
            text_content = f"{product.title} {product.category} {product.brand} {' '.join(product.tags)} {product.description}"
            text_features.append(text_content)
            
            # Numerical features: price (normalized)
            numerical_features.append([product.price])
        
        # TF-IDF for text features
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        text_vectors = self.tfidf_vectorizer.fit_transform(text_features)
        
        # Normalize numerical features
        numerical_vectors = self.scaler.fit_transform(numerical_features)
        
        # Combine features (text similarity weighted 0.8, price similarity 0.2)
        text_similarity = cosine_similarity(text_vectors)
        price_similarity = cosine_similarity(numerical_vectors)
        
        # Combined similarity matrix
        self.product_similarity_matrix = 0.8 * text_similarity + 0.2 * price_similarity
        
        logger.info("Built content-based similarity matrix")
    
    def build_collaborative_matrix(self):
        """Build user-item interaction matrix for collaborative filtering."""
        
        # Create user-item matrix from interactions
        users = list(set([i.user_id for i in self.interactions if i.interaction_type == 'purchase']))
        products = list(self.products.keys())
        
        matrix = np.zeros((len(users), len(products)))
        user_to_idx = {user: idx for idx, user in enumerate(users)}
        product_to_idx = {pid: idx for idx, pid in enumerate(products)}
        
        for interaction in self.interactions:
            if interaction.interaction_type == 'purchase' and interaction.user_id in user_to_idx:
                user_idx = user_to_idx[interaction.user_id]
                product_idx = product_to_idx[interaction.product_id]
                matrix[user_idx][product_idx] = 1
        
        self.interaction_matrix = matrix
        self.user_to_idx = user_to_idx
        self.product_to_idx = product_to_idx
        
        logger.info("Built collaborative filtering matrix")
    
    def get_content_based_recommendations(self, product_id: str, num_recommendations: int = 5) -> List[Recommendation]:
        """Get content-based recommendations for a product."""
        
        if product_id not in self.products:
            return []
        
        product_list = list(self.products.keys())
        product_idx = product_list.index(product_id)
        
        # Get similarity scores for the target product
        similarity_scores = self.product_similarity_matrix[product_idx]
        
        # Get top similar products (excluding the target product itself)
        similar_indices = np.argsort(similarity_scores)[::-1][1:num_recommendations+1]
        
        recommendations = []
        for idx in similar_indices:
            similar_product_id = product_list[idx]
            score = similarity_scores[idx]
            
            recommendations.append(Recommendation(
                product_id=similar_product_id,
                score=float(score),
                reason=f"Similar to {self.products[product_id].title}",
                algorithm="content_based"
            ))
        
        return recommendations
    
    def get_collaborative_recommendations(self, product_id: str, num_recommendations: int = 5) -> List[Recommendation]:
        """Get collaborative filtering recommendations."""
        
        if self.interaction_matrix is None or product_id not in self.product_to_idx:
            return []
        
        product_idx = self.product_to_idx[product_id]
        
        # Find users who purchased this product
        users_who_bought = np.where(self.interaction_matrix[:, product_idx] == 1)[0]
        
        if len(users_who_bought) == 0:
            return []
        
        # Count how often other products were bought by these users
        product_counts = np.sum(self.interaction_matrix[users_who_bought], axis=0)
        
        # Get top products (excluding the target product)
        product_counts[product_idx] = 0  # Exclude the target product
        top_indices = np.argsort(product_counts)[::-1][:num_recommendations]
        
        product_list = list(self.products.keys())
        recommendations = []
        
        for idx in top_indices:
            if product_counts[idx] > 0:
                recommended_product_id = product_list[idx]
                score = product_counts[idx] / len(users_who_bought)
                
                recommendations.append(Recommendation(
                    product_id=recommended_product_id,
                    score=float(score),
                    reason="Customers also bought",
                    algorithm="collaborative"
                ))
        
        return recommendations
    
    def get_popular_recommendations(self, num_recommendations: int = 5) -> List[Recommendation]:
        """Get popular products as fallback recommendations."""
        
        # Count purchases for each product
        purchase_counts = {}
        for interaction in self.interactions:
            if interaction.interaction_type == 'purchase':
                purchase_counts[interaction.product_id] = purchase_counts.get(interaction.product_id, 0) + 1
        
        # Sort by popularity
        sorted_products = sorted(purchase_counts.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for product_id, count in sorted_products[:num_recommendations]:
            recommendations.append(Recommendation(
                product_id=product_id,
                score=float(count),
                reason="Popular product",
                algorithm="popularity"
            ))
        
        return recommendations
    
    def get_hybrid_recommendations(self, product_id: str, num_recommendations: int = 5) -> List[Recommendation]:
        """Get hybrid recommendations combining multiple approaches."""
        
        all_recommendations = []
        
        # Get recommendations from different algorithms
        content_recs = self.get_content_based_recommendations(product_id, num_recommendations)
        collab_recs = self.get_collaborative_recommendations(product_id, num_recommendations)
        popular_recs = self.get_popular_recommendations(num_recommendations)
        
        # Combine and weight recommendations
        recommendation_dict = {}
        
        # Content-based (weight: 0.4)
        for rec in content_recs:
            recommendation_dict[rec.product_id] = recommendation_dict.get(rec.product_id, 0) + 0.4 * rec.score
        
        # Collaborative (weight: 0.4)
        for rec in collab_recs:
            recommendation_dict[rec.product_id] = recommendation_dict.get(rec.product_id, 0) + 0.4 * rec.score
        
        # Popular (weight: 0.2)
        for rec in popular_recs:
            if rec.product_id != product_id:  # Don't recommend the same product
                recommendation_dict[rec.product_id] = recommendation_dict.get(rec.product_id, 0) + 0.2 * (rec.score / 10)
        
        # Sort by combined score
        sorted_recommendations = sorted(recommendation_dict.items(), key=lambda x: x[1], reverse=True)
        
        # Create final recommendation objects
        for product_id_rec, score in sorted_recommendations[:num_recommendations]:
            if product_id_rec != product_id:  # Don't recommend the same product
                all_recommendations.append(Recommendation(
                    product_id=product_id_rec,
                    score=score,
                    reason="Hybrid recommendation",
                    algorithm="hybrid"
                ))
        
        return all_recommendations[:num_recommendations]
    
    def get_recommendations_for_product(self, product_id: str, algorithm: str = "hybrid", num_recommendations: int = 5) -> Dict[str, Any]:
        """Main method to get recommendations for a product."""
        
        if product_id not in self.products:
            return {
                "error": f"Product {product_id} not found",
                "recommendations": []
            }
        
        # Get recommendations based on algorithm
        if algorithm == "content":
            recommendations = self.get_content_based_recommendations(product_id, num_recommendations)
        elif algorithm == "collaborative":
            recommendations = self.get_collaborative_recommendations(product_id, num_recommendations)
        elif algorithm == "popularity":
            recommendations = self.get_popular_recommendations(num_recommendations)
        else:  # hybrid
            recommendations = self.get_hybrid_recommendations(product_id, num_recommendations)
        
        # Format response
        result = {
            "target_product": {
                "id": product_id,
                "title": self.products[product_id].title,
                "price": self.products[product_id].price
            },
            "algorithm": algorithm,
            "recommendations": []
        }
        
        for rec in recommendations:
            if rec.product_id in self.products:
                product = self.products[rec.product_id]
                result["recommendations"].append({
                    "product_id": rec.product_id,
                    "title": product.title,
                    "price": product.price,
                    "category": product.category,
                    "score": rec.score,
                    "reason": rec.reason,
                    "algorithm": rec.algorithm
                })
        
        return result


def main():
    """Main function to demonstrate the recommendation engine."""
    
    print("🛍️  Recommendation Engine Prototype")
    print("=" * 50)
    
    # Initialize the recommendation engine
    engine = RecommendationEngine()
    
    # Load sample data
    engine.load_sample_data()
    
    # Build models
    engine.build_content_similarity()
    engine.build_collaborative_matrix()
    
    # Test recommendations for different products
    test_products = ["1", "4", "6"]
    algorithms = ["hybrid", "content", "collaborative"]
    
    for product_id in test_products:
        print(f"\n📦 Recommendations for Product {product_id}: {engine.products[product_id].title}")
        print("-" * 60)
        
        for algorithm in algorithms:
            print(f"\n🔍 {algorithm.upper()} Algorithm:")
            recommendations = engine.get_recommendations_for_product(product_id, algorithm, 3)
            
            if "error" in recommendations:
                print(f"  ❌ {recommendations['error']}")
                continue
            
            for i, rec in enumerate(recommendations["recommendations"], 1):
                print(f"  {i}. {rec['title']} (${rec['price']:.2f}) - Score: {rec['score']:.3f}")
                print(f"     Reason: {rec['reason']}")
    
    # Simulate real-time API endpoint
    print(f"\n🌐 Real-time API Simulation")
    print("-" * 30)
    
    # Example of how this would be called from an API endpoint
    def api_get_recommendations(product_id: str, algorithm: str = "hybrid", limit: int = 5):
        """Simulate API endpoint for getting recommendations."""
        try:
            result = engine.get_recommendations_for_product(product_id, algorithm, limit)
            return {
                "status": "success",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Test API simulation
    api_response = api_get_recommendations("1", "hybrid", 4)
    print(f"API Response for Product 1:")
    print(json.dumps(api_response, indent=2))


if __name__ == "__main__":
    main()
