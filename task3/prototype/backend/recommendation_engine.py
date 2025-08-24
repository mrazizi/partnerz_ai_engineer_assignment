"""Hybrid recommendation engine implementing the design from recommendation_design.md."""
import json
import math
import os
from typing import List, Dict, Any, Tuple
from embedding_service import EmbeddingService
from config import config

class RecommendationEngine:
    """Hybrid recommendation engine combining collaborative and content-based filtering."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.lift_scores = {}
        self.co_occurrence = {}
        self.products = {}
        self._load_data()
    
    def _load_data(self):
        """Load precomputed data files."""
        try:
            # Load lift scores
            with open("data/lift_scores.json", "r") as f:
                self.lift_scores = json.load(f)
            print(f"Loaded lift scores for {len(self.lift_scores)} products")
            
            # Load co-occurrence data
            with open("data/co_occurrence.json", "r") as f:
                self.co_occurrence = json.load(f)
            print(f"Loaded co-occurrence data for {len(self.co_occurrence)} products")
            
            # Load products
            with open("data/products.json", "r") as f:
                products_list = json.load(f)
                self.products = {p["id"]: p for p in products_list}
            print(f"Loaded {len(self.products)} products")
            
        except FileNotFoundError as e:
            print(f"Data file not found: {e}. Run data_fetcher.py first.")
            
    def get_collaborative_candidates(self, product_id: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get collaborative filtering candidates based on lift scores."""
        if product_id not in self.lift_scores:
            return []
        
        # Get products with highest lift scores
        product_lifts = self.lift_scores[product_id]
        sorted_products = sorted(product_lifts.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_products[:top_n]
    
    def get_content_candidates(self, product_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Get content-based candidates using similarity search."""
        similar_products = self.embedding_service.search_similar_products(product_id, top_k)
        
        return [(p["product_id"], p["similarity_score"]) for p in similar_products]
    
    def get_enrichment_candidates(self, collaborative_products: List[str], top_m: int = 5) -> List[Tuple[str, float]]:
        """Get enrichment candidates - products similar to collaborative candidates."""
        enrichment_candidates = []
        
        for collab_product_id in collaborative_products:
            similar_products = self.embedding_service.search_similar_products(collab_product_id, top_m)
            
            for similar_product in similar_products:
                enrichment_candidates.append((similar_product["product_id"], similar_product["similarity_score"]))
        
        # Remove duplicates and sort by similarity
        unique_candidates = {}
        for product_id, score in enrichment_candidates:
            if product_id not in unique_candidates or score > unique_candidates[product_id]:
                unique_candidates[product_id] = score
        
        sorted_candidates = sorted(unique_candidates.items(), key=lambda x: x[1], reverse=True)
        return sorted_candidates[:top_m]
    
    def calculate_hybrid_score(self, candidate_id: str, target_product_id: str, 
                              collaborative_candidates: List[str]) -> Dict[str, float]:
        """Calculate hybrid score for a candidate product."""
        scores = {
            "collaborative_score": 0.0,
            "content_score": 0.0,
            "enrichment_score": 0.0,
            "collaborative_interactions": 0
        }
        
        # Collaborative score (lift)
        if target_product_id in self.lift_scores and candidate_id in self.lift_scores[target_product_id]:
            scores["collaborative_score"] = self.lift_scores[target_product_id][candidate_id]
            # Get interaction count for display
            if target_product_id in self.co_occurrence and candidate_id in self.co_occurrence[target_product_id]:
                scores["collaborative_interactions"] = self.co_occurrence[target_product_id][candidate_id]
        
        # Content similarity score
        similar_products = self.embedding_service.search_similar_products(target_product_id, 50)
        for similar_product in similar_products:
            if similar_product["product_id"] == candidate_id:
                scores["content_score"] = similar_product["similarity_score"]
                break
        
        # Enrichment score (max similarity to collaborative candidates)
        max_enrichment = 0.0
        for collab_id in collaborative_candidates:
            if collab_id != candidate_id:
                similar_products = self.embedding_service.search_similar_products(collab_id, 50)
                for similar_product in similar_products:
                    if similar_product["product_id"] == candidate_id:
                        max_enrichment = max(max_enrichment, similar_product["similarity_score"])
                        break
        scores["enrichment_score"] = max_enrichment
        
        return scores
    
    def generate_recommendations(self, product_id: str) -> Dict[str, Any]:
        """Generate hybrid recommendations for a product."""
        if product_id not in self.products:
            return {"error": f"Product {product_id} not found"}
        
        # Step 1: Get collaborative candidates
        collaborative_candidates = self.get_collaborative_candidates(product_id, config.TOP_K_SIMILAR)
        collab_product_ids = [pid for pid, _ in collaborative_candidates]
        
        # Step 2: Get content-based candidates
        content_candidates = self.get_content_candidates(product_id, config.TOP_K_SIMILAR)
        
        # Step 3: Get enrichment candidates
        enrichment_candidates = self.get_enrichment_candidates(collab_product_ids, config.TOP_M_ENRICHMENT)
        
        # Step 4: Combine all candidates
        all_candidates = set()
        all_candidates.update([pid for pid, _ in collaborative_candidates])
        all_candidates.update([pid for pid, _ in content_candidates])
        all_candidates.update([pid for pid, _ in enrichment_candidates])
        
        # Remove the original product
        all_candidates.discard(product_id)
        
        # Step 5: Score all candidates
        scored_candidates = []
        for candidate_id in all_candidates:
            if candidate_id in self.products:  # Ensure product exists
                scores = self.calculate_hybrid_score(candidate_id, product_id, collab_product_ids)
                
                # Calculate weighted final score
                final_score = (
                    config.COLLABORATIVE_WEIGHT * scores["collaborative_score"] +
                    config.CONTENT_WEIGHT * scores["content_score"] +
                    config.ENRICHMENT_WEIGHT * scores["enrichment_score"]
                )
                
                candidate_info = {
                    "product_id": candidate_id,
                    "product_info": self.products[candidate_id],
                    "final_score": final_score,
                    "score_breakdown": scores
                }
                scored_candidates.append(candidate_info)
        
        # Step 6: Sort and return top recommendations
        scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)
        top_recommendations = scored_candidates[:config.TOP_N_RECOMMENDATIONS]
        
        return {
            "target_product": self.products[product_id],
            "recommendations": top_recommendations,
            "debug_info": {
                "collaborative_candidates_count": len(collaborative_candidates),
                "content_candidates_count": len(content_candidates),
                "enrichment_candidates_count": len(enrichment_candidates),
                "total_candidates": len(all_candidates)
            }
        }
    
    def generate_all_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations for all products."""
        print("Generating recommendations for all products...")
        all_recommendations = {}
        
        for i, product_id in enumerate(self.products.keys()):
            print(f"Processing {i+1}/{len(self.products)}: {product_id}")
            recommendations = self.generate_recommendations(product_id)
            all_recommendations[product_id] = recommendations
        
        # Save to file
        output_file = "data/recommendations.json"
        os.makedirs("data", exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(all_recommendations, f, indent=2)
        
        print(f"Generated recommendations for {len(all_recommendations)} products")
        print(f"Saved to {output_file}")
        
        return {
            "total_products": len(all_recommendations),
            "output_file": output_file
        }

if __name__ == "__main__":
    engine = RecommendationEngine()
    result = engine.generate_all_recommendations()
    print(f"Recommendation generation completed: {result}")
