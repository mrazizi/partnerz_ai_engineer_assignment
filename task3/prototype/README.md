# Task 3: Product Recommendation System Prototype

## Overview
A hybrid recommendation system that combines collaborative filtering and content-based approaches using vector embeddings, lift scores, and enrichment techniques to provide personalized product recommendations for e-commerce platforms.

## Technologies Used

### Backend
- **FastAPI**: RESTful API framework for recommendation endpoints
- **Qdrant**: Vector database for similarity search and embeddings
- **OpenAI**: Text embeddings (text-embedding-3-small) for content-based filtering
- **Pandas/NumPy**: Data processing and mathematical operations
- **Pydantic**: Data validation and request/response models

### Frontend
- **Streamlit**: Interactive web interface with data visualization
- **Plotly**: Interactive charts and score breakdown visualizations
- **Requests**: HTTP client for backend communication

### Infrastructure
- **Docker & Docker Compose**: Containerization (Qdrant only)
- **Uvicorn**: ASGI server for FastAPI
- **Streamlit Server**: Web server for frontend

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
                       │ (Embeddings)    │
                       └─────────────────┘
```

## Workflow

### 1. Data Pipeline
```
Shopify Products → Data Fetcher → Embeddings → Qdrant + Precomputed Scores
```

### 2. Recommendation Generation
```
Product Query → Collaborative Candidates → Content Candidates → Enrichment → Hybrid Scoring → Top Recommendations
```

### 3. Hybrid Algorithm
1. **Collaborative Filtering**: Uses lift scores from co-occurrence analysis
2. **Content-Based**: Vector similarity search using product embeddings
3. **Enrichment**: Products similar to collaborative candidates
4. **Hybrid Scoring**: Weighted combination of all three approaches
5. **Ranking**: Final recommendations sorted by hybrid scores

## Design Components

### Backend Services
- **RecommendationEngine**: Core hybrid recommendation logic
- **EmbeddingService**: OpenAI embeddings and Qdrant vector operations
- **DataFetcher**: Shopify product data collection
- **FastAPI Endpoints**: `/recommendations`, `/products`, `/stats`

### Frontend Features
- **Product Selection**: Dropdown with product catalog
- **Recommendation Display**: Rich product cards with score breakdowns
- **Visual Analytics**: Interactive charts for score components
- **System Statistics**: Qdrant status and data metrics

### Data Processing
- **Lift Scores**: Association rule mining for collaborative filtering
- **Co-occurrence Matrix**: Product interaction patterns
- **Vector Embeddings**: Product text representations
- **Precomputed Recommendations**: Cached results for performance

## How to Run

### Option 1: Docker (Qdrant only)
```bash
cd task3/prototype
docker-compose up -d
```

### Option 2: Manual Start
```bash
# Backend
cd task3/prototype/backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd task3/prototype/frontend
streamlit run app.py --server.port 8501
```

Access the application at:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Qdrant**: http://localhost:6333/dashboard

## Key Features
- ✅ Hybrid recommendation algorithm
- ✅ Collaborative filtering with lift scores
- ✅ Content-based filtering with embeddings
- ✅ Enrichment techniques
- ✅ Precomputed recommendations
- ✅ Real-time scoring breakdown
- ✅ Interactive data visualization
- ✅ Vector similarity search
- ✅ Docker containerization
