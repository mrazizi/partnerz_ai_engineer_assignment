from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
from rag_service import RAGService
from data_ingestion import DataIngestionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Intercom RAG API",
    description="RAG system for Intercom Help Center articles",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = None
data_ingestion_service = None

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str = ""
    sources: List[Dict[str, Any]]
    query: str
    error: str = None

class IngestionRequest(BaseModel):
    json_path: str = None

class IngestionResponse(BaseModel):
    status: str
    message: str
    error: str = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global rag_service, data_ingestion_service
    try:
        logger.info("Initializing services...")
        rag_service = RAGService()
        data_ingestion_service = DataIngestionService()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Intercom RAG API is running",
        "version": "1.0.0",
        "endpoints": {
            "query": "/query",
            "ingest": "/ingest",
            "search": "/search",
            "info": "/info"
        }
    }

@app.post("/query", response_model=QueryResponse)
async def query_articles(request: QueryRequest):
    """Query the RAG system with a question."""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG service not initialized")
        
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        result = rag_service.query(request.question)
        logger.info(f"RAG service returned: {result}")
        
        if result.get("answer") is None:
            result["answer"] = ""
        
        response = QueryResponse(**result)
        logger.info(f"FastAPI response: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_data(request: IngestionRequest = None):
    """Ingest and index articles data into Qdrant."""
    try:
        if not data_ingestion_service:
            raise HTTPException(status_code=500, detail="Data ingestion service not initialized")
        
        json_path = request.json_path if request else None
        data_ingestion_service.ingest_data(json_path)
        
        return IngestionResponse(
            status="success",
            message="Data ingestion completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in ingest endpoint: {e}")
        return IngestionResponse(
            status="error",
            message="Data ingestion failed",
            error=str(e)
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        status = "healthy"
        details = {}
        
        if rag_service:
            collection_info = rag_service.get_collection_info()
            details["qdrant"] = collection_info.get("status", "unknown")
        else:
            status = "unhealthy"
            details["rag_service"] = "not_initialized"
        
        return {
            "status": status,
            "details": details
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

