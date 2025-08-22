#!/usr/bin/env python3
"""
Shopify Integration for Recommendation Engine
============================================

This script demonstrates how to integrate the recommendation engine with
Shopify storefront data using the MCP (Model Context Protocol) approach
similar to Task 2.

Features:
- Fetch real product data from Shopify storefront
- Generate recommendations based on real data
- Post recommendations to an endpoint
- Real-time recommendation serving
"""

import json
import requests
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import time
from recommendation_engine import RecommendationEngine, Product, UserInteraction

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShopifyRecommendationClient:
    """Client for integrating recommendations with Shopify storefront."""
    
    def __init__(self, store_url: str = "amirtest100.myshopify.com"):
        self.store_url = store_url
        self.mcp_endpoint = f"https://{self.store_url}/api/mcp"
        self.headers = {"Content-Type": "application/json"}
        self.engine = RecommendationEngine()
        
    def _make_mcp_request(self, tool_name: str, arguments: Dict = None) -> Dict[str, Any]:
        """Make MCP tool request to Shopify's built-in MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        try:
            response = requests.post(
                self.mcp_endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP server error: {result['error']}")
            
            return result.get("result", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MCP server connection failed: {str(e)}")
            return {}
    
    def fetch_products_from_shopify(self, query: str = "", limit: int = 20) -> List[Product]:
        """Fetch products from Shopify storefront using MCP."""
        
        logger.info(f"Fetching products from Shopify: {query}")
        
        # Use the search_shop_catalog tool
        arguments = {
            "query": query or "shirt",  # Default search to get some products
            "context": f"Fetching products for recommendation system"
        }
        
        response = self._make_mcp_request("search_shop_catalog", arguments)
        
        if not response or "content" not in response:
            logger.warning("No products returned from Shopify")
            return []
        
        try:
            products_data = json.loads(response["content"][0]["text"])["products"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing Shopify response: {e}")
            return []
        
        products = []
        for product_data in products_data[:limit]:
            try:
                # Extract product information
                product = Product(
                    id=product_data["product_id"],
                    title=product_data["title"],
                    category=product_data.get("product_type", "General"),
                    price=float(product_data.get("price_range", {}).get("min", "0.00")),
                    brand=product_data.get("vendor", "Unknown"),
                    tags=product_data.get("tags", []),
                    description=product_data.get("description", "")
                )
                products.append(product)
                
            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing product data: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(products)} products")
        return products
    
    def load_shopify_data(self):
        """Load product data from Shopify and build recommendation models."""
        
        # Fetch different categories of products
        search_queries = ["shirt", "shoes", "jacket", "jeans", "accessories"]
        all_products = []
        
        for query in search_queries:
            products = self.fetch_products_from_shopify(query, limit=10)
            all_products.extend(products)
        
        # Remove duplicates
        unique_products = {p.id: p for p in all_products}
        
        # Load products into recommendation engine
        self.engine.products = unique_products
        
        # Generate some sample interactions for demonstration
        self._generate_sample_interactions()
        
        # Build recommendation models
        if len(self.engine.products) > 0:
            self.engine.build_content_similarity()
            self.engine.build_collaborative_matrix()
            logger.info(f"Loaded {len(self.engine.products)} products and built recommendation models")
        else:
            logger.warning("No products loaded - using fallback data")
            self.engine.load_sample_data()
            self.engine.build_content_similarity()
            self.engine.build_collaborative_matrix()
    
    def _generate_sample_interactions(self):
        """Generate sample user interactions for demonstration."""
        
        product_ids = list(self.engine.products.keys())
        if len(product_ids) < 2:
            return
        
        # Generate realistic interaction patterns
        sample_interactions = []
        users = [f"user_{i}" for i in range(1, 6)]
        
        for i, user_id in enumerate(users):
            session_id = f"session_{i}"
            
            # Each user views 2-4 products and buys 1-2
            viewed_products = product_ids[i*2:(i*2)+3] if i*2+3 <= len(product_ids) else product_ids[:3]
            
            for j, product_id in enumerate(viewed_products):
                # View interaction
                sample_interactions.append(UserInteraction(
                    user_id=user_id,
                    product_id=product_id,
                    interaction_type="view",
                    timestamp=datetime.now(),
                    session_id=session_id
                ))
                
                # Some products get purchased
                if j < 2:  # Buy first 2 viewed products
                    sample_interactions.append(UserInteraction(
                        user_id=user_id,
                        product_id=product_id,
                        interaction_type="purchase",
                        timestamp=datetime.now(),
                        session_id=session_id
                    ))
        
        self.engine.interactions = sample_interactions
        logger.info(f"Generated {len(sample_interactions)} sample interactions")
    
    def get_recommendations_api(self, product_id: str, algorithm: str = "hybrid", num_recommendations: int = 5) -> Dict[str, Any]:
        """API endpoint simulation for getting recommendations."""
        
        start_time = time.time()
        
        try:
            recommendations = self.engine.get_recommendations_for_product(
                product_id, algorithm, num_recommendations
            )
            
            processing_time = time.time() - start_time
            
            response = {
                "status": "success",
                "data": recommendations,
                "metadata": {
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "algorithm": algorithm,
                    "timestamp": datetime.now().isoformat(),
                    "store_url": self.store_url
                }
            }
            
            logger.info(f"Generated recommendations for product {product_id} in {processing_time:.3f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def post_recommendations_to_endpoint(self, endpoint_url: str, product_id: str, recommendations: Dict[str, Any]):
        """Post recommendations to an external endpoint."""
        
        payload = {
            "product_id": product_id,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                endpoint_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Successfully posted recommendations to {endpoint_url}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post recommendations: {e}")
            return {"error": str(e)}
    
    def run_real_time_demo(self):
        """Run a real-time demonstration of the recommendation system."""
        
        print("🚀 Real-time Shopify Recommendation Demo")
        print("=" * 50)
        
        # Load data from Shopify
        print("📥 Loading product data from Shopify...")
        self.load_shopify_data()
        
        if not self.engine.products:
            print("❌ No products loaded. Please check Shopify connection.")
            return
        
        # Get some products to test
        product_ids = list(self.engine.products.keys())[:3]
        
        print(f"\n🔍 Testing recommendations for {len(product_ids)} products")
        print("-" * 40)
        
        for product_id in product_ids:
            product = self.engine.products[product_id]
            print(f"\n📦 Product: {product.title} (ID: {product_id})")
            print(f"   Category: {product.category} | Price: ${product.price:.2f}")
            
            # Get recommendations
            result = self.get_recommendations_api(product_id, "hybrid", 3)
            
            if result["status"] == "success":
                recommendations = result["data"]["recommendations"]
                processing_time = result["metadata"]["processing_time_ms"]
                
                print(f"   ⚡ Generated in {processing_time}ms")
                print("   📋 Recommendations:")
                
                for i, rec in enumerate(recommendations, 1):
                    print(f"     {i}. {rec['title']} (${rec['price']:.2f}) - Score: {rec['score']:.3f}")
                
                # Simulate posting to an endpoint
                print("   📤 Posting to endpoint...")
                # In a real scenario, you would post to your recommendation storage endpoint
                # post_result = self.post_recommendations_to_endpoint("https://your-api.com/recommendations", product_id, result)
                print("   ✅ Posted successfully (simulated)")
                
            else:
                print(f"   ❌ Error: {result['message']}")
            
            time.sleep(1)  # Brief pause between requests
        
        print(f"\n✨ Demo completed! Processed {len(product_ids)} products")


def main():
    """Main function to run the Shopify integration demo."""
    
    # Initialize the Shopify recommendation client
    client = ShopifyRecommendationClient()
    
    # Run the real-time demo
    client.run_real_time_demo()
    
    print(f"\n💡 Integration Points:")
    print("- Fetch products from Shopify MCP endpoint")
    print("- Generate recommendations using hybrid algorithm")
    print("- Serve recommendations via API endpoint")
    print("- Post results to external recommendation storage")
    
    print(f"\n🔧 Production Implementation:")
    print("1. Set up scheduled jobs to fetch product data")
    print("2. Implement real-time interaction tracking")
    print("3. Create API endpoints for recommendation serving")
    print("4. Add caching layer for performance")
    print("5. Implement A/B testing framework")


if __name__ == "__main__":
    main()
