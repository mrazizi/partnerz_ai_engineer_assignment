# Task 1: Intercom Help Center RAG System

## Overview
A Retrieval-Augmented Generation (RAG) system that provides intelligent answers to questions about Intercom's help center articles using vector search and AI-powered responses.

## Technologies Used

### Backend
- **FastAPI**: RESTful API framework
- **Qdrant**: Vector database for similarity search
- **LangChain**: RAG orchestration framework
- **OpenAI**: Embeddings (text-embedding-3-small) and LLM (gpt-4o)
- **Pydantic**: Data validation and serialization

### Frontend
- **Streamlit**: Interactive web interface
- **Requests**: HTTP client for API communication

### Infrastructure
- **Docker & Docker Compose**: Containerization and orchestration

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Qdrant        │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (Vector DB)   │
│   Port: 8501    │    │   Port: 8000    │    │   Port: 6333    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │ (Embeddings &   │
                       │     GPT-4o)     │
                       └─────────────────┘
```

## Workflow

### 1. Data Ingestion
```
Articles JSON → DataIngestionService → Qdrant Vector Store
```

### 2. Query Processing
```
User Question → Frontend → Backend → RAG Service → Qdrant Search → OpenAI LLM → Response
```

### 3. RAG Pipeline
1. **Question Input**: User submits question via Streamlit interface
2. **Vector Search**: Qdrant finds similar articles using embeddings
3. **Context Retrieval**: Top 5 most relevant articles retrieved
4. **LLM Generation**: OpenAI GPT-4o generates answer using context
5. **Response**: Answer + source articles returned to user

## Design Components

### Backend Services
- **RAGService**: Core RAG logic with LangChain integration
- **DataIngestionService**: Handles article indexing into Qdrant
- **FastAPI Endpoints**: `/query`, `/ingest`, `/search`, `/info`

### Frontend Features
- **Interactive Chat Interface**: Clean, responsive UI
- **Source Attribution**: Shows referenced articles
- **System Status**: Backend connectivity monitoring
- **Data Ingestion**: One-click article indexing

### Vector Database
- **Collection**: `intercom_articles`
- **Embeddings**: OpenAI text-embedding-3-small
- **Search**: Similarity-based retrieval (k=5)

## How to Run

```bash
cd task1
docker-compose up -d --build
```

Access the application at:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Qdrant**: http://localhost:6333/dashboard

## Key Features
- ✅ Real-time question answering
- ✅ Source article attribution
- ✅ Vector similarity search
- ✅ Docker containerization
- ✅ RESTful API design
- ✅ Interactive web interface
