import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    
    # Qdrant Configuration
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "product_recommendations")
    
    # Shopify Configuration
    SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "amirtest100.myshopify.com")
    
    # Application Configuration
    EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
    VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "1536"))
    
    # Recommendation Configuration
    COLLABORATIVE_WEIGHT = float(os.getenv("COLLABORATIVE_WEIGHT", "0.4"))
    CONTENT_WEIGHT = float(os.getenv("CONTENT_WEIGHT", "0.4"))
    ENRICHMENT_WEIGHT = float(os.getenv("ENRICHMENT_WEIGHT", "0.2"))
    
    TOP_N_RECOMMENDATIONS = int(os.getenv("TOP_N_RECOMMENDATIONS", "5"))
    TOP_K_SIMILAR = int(os.getenv("TOP_K_SIMILAR", "10"))
    TOP_M_ENRICHMENT = int(os.getenv("TOP_M_ENRICHMENT", "5"))

config = Config()
