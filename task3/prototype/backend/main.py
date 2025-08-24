"""FastAPI backend for the recommendation system prototype."""
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from pydantic import BaseModel
from recommendation_engine import RecommendationEngine
from embedding_service import EmbeddingService

app = FastAPI(title="Product Recommendation System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
recommendation_engine = RecommendationEngine()
embedding_service = EmbeddingService()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Product Recommendation System API", "status": "running"}

@app.get("/products")
async def get_products() -> List[Dict[str, Any]]:
    """Get all products."""
    try:
        with open("data/products.json", "r") as f:
            products = json.load(f)
        return products
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Products data not found")

@app.get("/products/{product_id}")
async def get_product(product_id: str) -> Dict[str, Any]:
    """Get a specific product by ID."""
    try:
        with open("data/products.json", "r") as f:
            products = json.load(f)
        
        for product in products:
            if product["id"] == product_id:
                return product
        
        raise HTTPException(status_code=404, detail="Product not found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Products data not found")

class RecommendationRequest(BaseModel):
    product_id: str

@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest) -> Dict[str, Any]:
    """Get recommendations for a specific product."""
    product_id = request.product_id
    print(f"Received product_id: '{product_id}'")
    try:
        # First try to get precomputed recommendations
        try:
            with open("data/recommendations.json", "r") as f:
                all_recommendations = json.load(f)
            
            print(f"Available product IDs in recommendations: {list(all_recommendations.keys())[:5]}...")
            
            if product_id in all_recommendations:
                print(f"Found product {product_id} in precomputed recommendations")
                return all_recommendations[product_id]
            else:
                print(f"Product {product_id} not found in precomputed recommendations")
        except FileNotFoundError:
            print("Precomputed recommendations file not found, falling back to generation")
            pass  # Fall back to generating recommendations
        
        # If not found in precomputed, generate on-the-fly
        recommendations = recommendation_engine.generate_recommendations(product_id)
        
        if "error" in recommendations:
            raise HTTPException(status_code=404, detail=recommendations["error"])
        
        return recommendations
    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/recommendations")
async def get_all_recommendations() -> Dict[str, Any]:
    """Get all precomputed recommendations."""
    try:
        with open("data/recommendations.json", "r") as f:
            recommendations = json.load(f)
        return recommendations
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Recommendations data not found")

@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get system statistics."""
    try:
        # Get Qdrant stats
        qdrant_stats = embedding_service.get_collection_stats()
        
        # Get data file stats
        stats = {"qdrant": qdrant_stats}
        
        try:
            with open("data/products.json", "r") as f:
                products = json.load(f)
            stats["products_count"] = len(products)
        except FileNotFoundError:
            stats["products_count"] = 0
        
        try:
            with open("data/interactions.json", "r") as f:
                interactions = json.load(f)
            stats["interactions_count"] = len(interactions)
        except FileNotFoundError:
            stats["interactions_count"] = 0
        
        try:
            with open("data/recommendations.json", "r") as f:
                recommendations = json.load(f)
            stats["recommendations_count"] = len(recommendations)
        except FileNotFoundError:
            stats["recommendations_count"] = 0
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.post("/generate-recommendations")
async def generate_recommendations() -> Dict[str, Any]:
    """Generate recommendations for all products (long-running operation)."""
    try:
        result = recommendation_engine.generate_all_recommendations()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
