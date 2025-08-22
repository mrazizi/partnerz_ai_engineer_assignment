import json
import logging
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionService:
    def __init__(self):
        self.client = QdrantClient(url=config.QDRANT_URL)
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=config.OPENAI_API_KEY,
            model=config.EMBEDDINGS_MODEL
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def load_articles(self, json_path: str) -> List[Dict]:
        """Load articles from JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            logger.info(f"Loaded {len(articles)} articles from {json_path}")
            return articles
        except Exception as e:
            logger.error(f"Error loading articles: {e}")
            raise
    
    def create_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            vector_size = config.VECTOR_SIZE
            
            if config.QDRANT_COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=config.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {config.QDRANT_COLLECTION_NAME} with vector size {vector_size}")
            else:
                collection_info = self.client.get_collection(config.QDRANT_COLLECTION_NAME)
                existing_size = collection_info.config.params.vectors.size
                if existing_size != vector_size:
                    logger.warning(f"Collection exists with vector size {existing_size}, but model expects {vector_size}")
                    logger.info("Consider deleting and recreating the collection for proper vector size")
                else:
                    logger.info(f"Collection {config.QDRANT_COLLECTION_NAME} already exists with correct vector size")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def process_and_embed_articles(self, articles: List[Dict]) -> List[PointStruct]:
        """Process articles into chunks and generate embeddings."""
        points = []
        point_id = 0
        
        for article_idx, article in enumerate(articles):
            try:
                full_text = f"Title: {article['title']}\n\nContent: {article['content']}"
                chunks = self.text_splitter.split_text(full_text)
                
                for chunk_idx, chunk in enumerate(chunks):
                    if not chunk or chunk.strip() == "":
                        logger.warning(f"Skipping empty chunk {chunk_idx} for article {article_idx}")
                        continue
                    
                    embedding = self.embeddings.embed_query(chunk)
                    
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "content": chunk,
                            "metadata": {
                                "article_id": article_idx,
                                "chunk_id": chunk_idx,
                                "title": article["title"],
                                "url": article["url"],
                                "full_content": article["content"]
                            }
                        }
                    )
                    points.append(point)
                    point_id += 1
                
                if article_idx % 10 == 0:
                    logger.info(f"Processed {article_idx + 1}/{len(articles)} articles")
                    
            except Exception as e:
                logger.error(f"Error processing article {article_idx}: {e}")
                continue
        
        logger.info(f"Generated {len(points)} chunks from {len(articles)} articles")
        return points
    
    def index_data(self, points: List[PointStruct], batch_size: int = 100):
        """Index data into Qdrant."""
        try:
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=config.QDRANT_COLLECTION_NAME,
                    points=batch
                )
                logger.info(f"Indexed batch {i // batch_size + 1}/{(len(points) + batch_size - 1) // batch_size}")
            
            logger.info(f"Successfully indexed {len(points)} points")
        except Exception as e:
            logger.error(f"Error indexing data: {e}")
            raise
    
    def ingest_data(self, json_path: str = config.ARTICLES_JSON_PATH):
        """Complete data ingestion pipeline."""
        logger.info("Starting data ingestion pipeline...")

        articles = self.load_articles(json_path)
        # TODO: use 10 articles for testing
        # TODO: chunk and index at the same time
        articles = articles[:10]
        self.create_collection()
        points = self.process_and_embed_articles(articles)
        self.index_data(points)
        
        logger.info("Data ingestion completed successfully!")

