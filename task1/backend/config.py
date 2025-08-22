import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
    
    # Qdrant Configuration
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "intercom_articles")
    
    # Application Configuration
    EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
    CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-5-2025-08-07")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "1536"))
    
    # Data Configuration
    ARTICLES_JSON_PATH = os.getenv("ARTICLES_JSON_PATH", "../articles.json")

config = Config()
