"""Data fetcher for products and interaction data."""
import json
import os
import random
from typing import List, Dict, Any
from shopify_client import ShopifyStorefrontClient
from embedding_service import EmbeddingService

class DataFetcher:
    """Fetches products from Shopify and creates mock interaction data."""
    
    def __init__(self):
        self.shopify_client = ShopifyStorefrontClient()
        self.embedding_service = EmbeddingService()
    
    def fetch_and_store_products(self, target_count: int = 500) -> Dict[str, Any]:
        """Fetch products from Shopify and store embeddings."""
        print(f"Fetching {target_count} products from Shopify...")
        
        # Fetch products from Shopify
        products = self.shopify_client.get_all_products(target_count)
        
        # Convert to dict format for processing
        products_dict = []
        for product in products:
            product_dict = {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "handle": product.handle,
                "price": product.price,
                "currency": product.currency,
                "images": product.images,
                "variants": product.variants
            }
            products_dict.append(product_dict)
        
        # Save products to JSON file
        products_file = "data/products.json"
        os.makedirs("data", exist_ok=True)
        with open(products_file, "w") as f:
            json.dump(products_dict, f, indent=2)
        
        print(f"Saved {len(products_dict)} products to {products_file}")
        
        # Process embeddings
        print("Generating embeddings and storing in Qdrant...")
        embedding_result = self.embedding_service.process_products(products_dict)
        
        return {
            "products_fetched": len(products_dict),
            "embedding_result": embedding_result
        }
    
    def generate_mock_interactions(self, products: List[Dict[str, Any]], num_users: int = 1000) -> List[Dict[str, Any]]:
        """Generate mock interaction data for collaborative filtering."""
        print(f"Generating mock interactions for {num_users} users...")
        
        interactions = []
        product_ids = [p["id"] for p in products]
        
        for user_id in range(num_users):
            # Each user interacts with 2-10 products
            num_interactions = random.randint(2, 10)
            user_products = random.sample(product_ids, min(num_interactions, len(product_ids)))
            
            for product_id in user_products:
                # Create different types of interactions
                interaction_type = random.choice(["view", "add_to_cart", "purchase"])
                
                interaction = {
                    "user_id": f"user_{user_id}",
                    "product_id": product_id,
                    "interaction_type": interaction_type,
                    "timestamp": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                }
                interactions.append(interaction)
        
        # Save interactions to JSON file
        interactions_file = "data/interactions.json"
        os.makedirs("data", exist_ok=True)
        with open(interactions_file, "w") as f:
            json.dump(interactions, f, indent=2)
        
        print(f"Generated {len(interactions)} interactions and saved to {interactions_file}")
        return interactions
    
    def create_co_occurrence_matrix(self, interactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Create co-occurrence matrix from interactions."""
        print("Creating co-occurrence matrix...")
        
        # Group interactions by user
        user_products = {}
        for interaction in interactions:
            user_id = interaction["user_id"]
            product_id = interaction["product_id"]
            
            if user_id not in user_products:
                user_products[user_id] = set()
            user_products[user_id].add(product_id)
        
        # Create co-occurrence matrix
        co_occurrence = {}
        
        for user_id, products in user_products.items():
            products_list = list(products)
            
            # For each pair of products this user interacted with
            for i, product_a in enumerate(products_list):
                if product_a not in co_occurrence:
                    co_occurrence[product_a] = {}
                
                for j, product_b in enumerate(products_list):
                    if i != j:  # Don't count product with itself
                        if product_b not in co_occurrence[product_a]:
                            co_occurrence[product_a][product_b] = 0
                        co_occurrence[product_a][product_b] += 1
        
        # Save co-occurrence matrix
        cooccurrence_file = "data/co_occurrence.json"
        os.makedirs("data", exist_ok=True)
        with open(cooccurrence_file, "w") as f:
            json.dump(co_occurrence, f, indent=2)
        
        print(f"Created co-occurrence matrix and saved to {cooccurrence_file}")
        return co_occurrence
    
    def calculate_lift_scores(self, co_occurrence: Dict[str, Dict[str, int]], 
                            interactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate lift scores for product pairs."""
        print("Calculating lift scores...")
        
        # Count total transactions and product frequencies
        total_transactions = len(set(interaction["user_id"] for interaction in interactions))
        product_counts = {}
        
        for interaction in interactions:
            product_id = interaction["product_id"]
            if product_id not in product_counts:
                product_counts[product_id] = set()
            product_counts[product_id].add(interaction["user_id"])
        
        # Convert to frequencies
        product_frequencies = {pid: len(users) for pid, users in product_counts.items()}
        
        # Calculate lift scores
        lift_scores = {}
        
        for product_a, related_products in co_occurrence.items():
            lift_scores[product_a] = {}
            
            for product_b, co_freq in related_products.items():
                # Lift = P(A,B) / (P(A) * P(B))
                # Where P(A,B) = co_frequency / total_transactions
                # P(A) = frequency_A / total_transactions
                # P(B) = frequency_B / total_transactions
                
                freq_a = product_frequencies.get(product_a, 1)
                freq_b = product_frequencies.get(product_b, 1)
                
                prob_a = freq_a / total_transactions
                prob_b = freq_b / total_transactions
                prob_ab = co_freq / total_transactions
                
                if prob_a > 0 and prob_b > 0:
                    lift = prob_ab / (prob_a * prob_b)
                else:
                    lift = 0.0
                
                lift_scores[product_a][product_b] = lift
        
        # Save lift scores
        lift_file = "data/lift_scores.json"
        os.makedirs("data", exist_ok=True)
        with open(lift_file, "w") as f:
            json.dump(lift_scores, f, indent=2)
        
        print(f"Calculated lift scores and saved to {lift_file}")
        return lift_scores

if __name__ == "__main__":
    fetcher = DataFetcher()
    
    # Fetch and embed products
    result = fetcher.fetch_and_store_products(500)
    print(f"Fetch result: {result}")
    
    # Load products for interaction generation
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    # Generate mock interactions
    interactions = fetcher.generate_mock_interactions(products, num_users=1000)
    
    # Create co-occurrence matrix and lift scores
    co_occurrence = fetcher.create_co_occurrence_matrix(interactions)
    lift_scores = fetcher.calculate_lift_scores(co_occurrence, interactions)
    
    print("Data fetching and processing completed!")
