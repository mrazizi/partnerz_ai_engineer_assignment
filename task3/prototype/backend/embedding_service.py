"""Embedding service for product text embeddings using OpenAI."""
import openai
import numpy as np
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import config

class EmbeddingService:
    """Service for generating and storing product embeddings."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.qdrant_client = QdrantClient(url=config.QDRANT_URL)
        self.collection_name = config.QDRANT_COLLECTION_NAME
        self._setup_collection()
    
    def _setup_collection(self):
        """Setup Qdrant collection for product embeddings."""
        try:
            # Check if collection exists
            self.qdrant_client.get_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' already exists")
        except Exception:
            # Create collection if it doesn't exist
            print(f"Creating collection '{self.collection_name}'")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=config.VECTOR_SIZE, distance=Distance.COSINE),
            )
    
    def generate_text_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = self.client.embeddings.create(
                input=text,
                model=config.EMBEDDINGS_MODEL
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * config.VECTOR_SIZE
    
    def create_product_text(self, product: Dict[str, Any]) -> str:
        """Create text representation of product for embedding."""
        title = product.get("title", "")
        description = product.get("description", "")
        
        # Clean and combine text
        text_parts = []
        if title:
            text_parts.append(f"Title: {title}")
        if description:
            text_parts.append(f"Description: {description}")
        
        return " ".join(text_parts)
    
    def store_product_embedding(self, product: Dict[str, Any], embedding: List[float]):
        """Store product embedding in Qdrant."""
        point = PointStruct(
            id=hash(product["id"]) % (2**31),  # Convert string ID to int
            vector=embedding,
            payload={
                "product_id": product["id"],
                "title": product["title"],
                "description": product["description"],
                "price": product["price"],
                "currency": product["currency"],
                "images": product["images"],
                "handle": product["handle"]
            }
        )
        
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
    
    def process_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process all products: generate embeddings and store them."""
        processed_count = 0
        failed_count = 0
        
        for i, product in enumerate(products):
            try:
                print(f"Processing product {i+1}/{len(products)}: {product['title']}")
                
                # Generate text for embedding
                product_text = self.create_product_text(product)
                
                # Generate embedding
                embedding = self.generate_text_embedding(product_text)
                
                # Store in Qdrant
                self.store_product_embedding(product, embedding)
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing product {product.get('id', 'unknown')}: {e}")
                failed_count += 1
        
        return {
            "processed": processed_count,
            "failed": failed_count,
            "total": len(products)
        }
    
    def search_similar_products(self, product_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar products using vector search."""
        try:
            # First, get the product's embedding
            search_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "product_id",
                            "match": {"value": product_id}
                        }
                    ]
                },
                limit=1,
                with_vectors=True
            )
            
            if not search_result[0]:
                return []
            
            product_vector = search_result[0][0].vector
            
            # Search for similar products
            similar_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=product_vector,
                limit=limit + 1,  # +1 to exclude the original product
                with_payload=True
            )
            
            # Filter out the original product and return results
            similar_products = []
            for result in similar_results:
                if result.payload["product_id"] != product_id:
                    similar_products.append({
                        "product_id": result.payload["product_id"],
                        "title": result.payload["title"],
                        "similarity_score": result.score,
                        "payload": result.payload
                    })
            
            return similar_products[:limit]
            
        except Exception as e:
            print(f"Error searching similar products for {product_id}: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "status": "connected"
            }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "status": "error",
                "error": str(e)
            }
