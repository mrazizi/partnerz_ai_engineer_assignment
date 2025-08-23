import json
import logging
import asyncio
from typing import List, Dict, Set
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from config import config
import hashlib

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
        
    def load_articles(self, json_path: str = None) -> List[Dict]:
        """Load articles from JSON file."""
        try:
            # Use default path if none provided
            if json_path is None:
                json_path = config.ARTICLES_JSON_PATH
                
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
    
    def get_existing_article_urls(self) -> Set[str]:
        """Get URLs of articles already in the collection."""
        try:
            # Scroll through all points to get existing article URLs
            result = self.client.scroll(
                collection_name=config.QDRANT_COLLECTION_NAME,
                limit=10000,  # Adjust based on your collection size
                with_payload=True,
                with_vectors=False
            )
            
            existing_urls = set()
            for point in result[0]:  # result is a tuple (points, next_page_offset)
                if point.payload and "metadata" in point.payload:
                    url = point.payload["metadata"].get("url")
                    if url:
                        existing_urls.add(url)
            
            logger.info(f"Found {len(existing_urls)} existing articles in collection")
            return existing_urls
            
        except Exception as e:
            logger.warning(f"Error getting existing articles (collection might be empty): {e}")
            return set()
    
    def filter_new_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filter out articles that already exist in the collection."""
        existing_urls = self.get_existing_article_urls()
        new_articles = [article for article in articles if article.get("url") not in existing_urls]
        
        skipped_count = len(articles) - len(new_articles)
        if skipped_count > 0:
            logger.info(f"Skipping {skipped_count} articles that already exist in collection")
        
        logger.info(f"Processing {len(new_articles)} new articles")
        return new_articles
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings in batches for better performance."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Generating embeddings for batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")
            
            try:
                # Use the batch embedding method
                embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(embeddings)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i // batch_size + 1}: {e}")
                # Generate embeddings one by one for this batch as fallback
                for text in batch:
                    try:
                        embedding = self.embeddings.embed_query(text)
                        all_embeddings.append(embedding)
                        await asyncio.sleep(0.05)  # Smaller delay for individual requests
                    except Exception as text_e:
                        logger.error(f"Error generating embedding for text: {text_e}")
                        # Use zero vector as fallback
                        all_embeddings.append([0.0] * config.VECTOR_SIZE)
        
        return all_embeddings
    
    async def process_and_embed_articles_async(self, articles: List[Dict]) -> List[PointStruct]:
        """Process articles into chunks and generate embeddings efficiently."""
        all_chunks = []
        chunk_metadata = []
        point_id_start = self.get_next_point_id()
        
        # First, process all articles into chunks
        for article_idx, article in enumerate(articles):
            try:
                full_text = f"Title: {article['title']}\n\nContent: {article['content']}"
                chunks = self.text_splitter.split_text(full_text)
                
                for chunk_idx, chunk in enumerate(chunks):
                    if not chunk or chunk.strip() == "":
                        logger.warning(f"Skipping empty chunk {chunk_idx} for article {article_idx}")
                        continue
                    
                    all_chunks.append(chunk)
                    chunk_metadata.append({
                        "article_idx": article_idx,
                        "chunk_idx": chunk_idx,
                        "article": article
                    })
                
                if article_idx % 10 == 0:
                    logger.info(f"Processed {article_idx + 1}/{len(articles)} articles into chunks")
                    
            except Exception as e:
                logger.error(f"Error processing article {article_idx}: {e}")
                continue
        
        logger.info(f"Generated {len(all_chunks)} chunks from {len(articles)} articles")
        
        # Generate embeddings in batches
        embeddings = await self.generate_embeddings_batch(all_chunks, batch_size=50)
        
        # Create PointStruct objects
        points = []
        for i, (chunk, metadata, embedding) in enumerate(zip(all_chunks, chunk_metadata, embeddings)):
            point = PointStruct(
                id=point_id_start + i,
                vector=embedding,
                payload={
                    "content": chunk,
                    "metadata": {
                        "article_id": metadata["article_idx"],
                        "chunk_id": metadata["chunk_idx"],
                        "title": metadata["article"]["title"],
                        "url": metadata["article"]["url"],
                        "full_content": metadata["article"]["content"]
                    }
                }
            )
            points.append(point)
        
        return points
    
    def get_next_point_id(self) -> int:
        """Get the next available point ID."""
        try:
            collection_info = self.client.get_collection(config.QDRANT_COLLECTION_NAME)
            return collection_info.points_count
        except:
            return 0
    
    async def index_data_batch(self, points: List[PointStruct], batch_size: int = 100):
        """Index data into Qdrant in batches with immediate persistence."""
        try:
            total_batches = (len(points) + batch_size - 1) // batch_size
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                
                try:
                    self.client.upsert(
                        collection_name=config.QDRANT_COLLECTION_NAME,
                        points=batch
                    )
                    logger.info(f"Indexed batch {i // batch_size + 1}/{total_batches} ({len(batch)} points)")
                    
                    # Small delay between batches
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error indexing batch {i // batch_size + 1}: {e}")
                    # Try to index points individually as fallback
                    for point in batch:
                        try:
                            self.client.upsert(
                                collection_name=config.QDRANT_COLLECTION_NAME,
                                points=[point]
                            )
                        except Exception as point_e:
                            logger.error(f"Error indexing individual point {point.id}: {point_e}")
            
            logger.info(f"Successfully indexed {len(points)} points")
            
        except Exception as e:
            logger.error(f"Error in batch indexing: {e}")
            raise
    
    async def ingest_data_async(self, json_path: str = None):
        """Complete async data ingestion pipeline."""
        logger.info("Starting async data ingestion pipeline...")

        # Load articles
        articles = self.load_articles(json_path)
        
        # Filter out existing articles
        new_articles = self.filter_new_articles(articles)
        
        if not new_articles:
            logger.info("No new articles to process")
            return
        
        # Create collection
        self.create_collection()
        
        # Process and embed articles in batches
        points = await self.process_and_embed_articles_async(new_articles)
        
        if not points:
            logger.info("No points to index")
            return
        
        # Index data in batches
        await self.index_data_batch(points)
        
        logger.info(f"Data ingestion completed successfully! Processed {len(new_articles)} new articles into {len(points)} chunks")
    
    def ingest_data(self, json_path: str = None):
        """Synchronous wrapper for backward compatibility."""
        return asyncio.run(self.ingest_data_async(json_path))