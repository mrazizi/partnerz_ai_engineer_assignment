# Product Recommendation System Prototype

This prototype implements the hybrid recommendation system described in `recommendation_design.md`. It combines collaborative filtering and content-based filtering to provide "Customers also bought/viewed" recommendations.

## Features

- **Hybrid Recommendation Algorithm**: Combines collaborative filtering (lift scores) with content-based filtering (embeddings)
- **Real Shopify Data**: Fetches actual product data from Shopify using MCP
- **Vector Embeddings**: Uses OpenAI text embeddings for content similarity
- **Interactive Frontend**: Streamlit-based UI showing score breakdowns
- **Mock Interaction Data**: Generates realistic user interaction patterns

## Architecture

```
├── backend/
│   ├── main.py              # FastAPI server
│   ├── recommendation_engine.py # Core recommendation logic
│   ├── embedding_service.py     # OpenAI embeddings + Qdrant
│   ├── shopify_client.py       # Shopify MCP client
│   ├── data_fetcher.py         # Data collection & preprocessing
│   └── config.py               # Configuration
├── frontend/
│   └── app.py                  # Streamlit UI
├── data/                       # Generated data files
└── docker-compose.yml          # Container orchestration
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Access to Shopify store (amirtest100.myshopify.com)

### Setup

1. **Clone and navigate to the prototype directory:**
   ```bash
   cd task3/prototype
   ```

2. **Set up environment variables:**
   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your OpenAI API key
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Run the data pipeline:**
   ```bash
   docker-compose exec backend python data_fetcher.py
   docker-compose exec backend python recommendation_engine.py
   ```

5. **Access the frontend:**
   - Frontend: http://localhost:8501
   - API: http://localhost:8000
   - Qdrant: http://localhost:6333

## Manual Setup (Development)

### Backend Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY="your_key_here"
   export QDRANT_URL="http://localhost:6333"
   ```

3. **Start Qdrant:**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant:latest
   ```

4. **Run data collection:**
   ```bash
   python data_fetcher.py
   ```

5. **Generate recommendations:**
   ```bash
   python recommendation_engine.py
   ```

6. **Start API server:**
   ```bash
   python main.py
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Start Streamlit:**
   ```bash
   streamlit run app.py
   ```

## Data Pipeline

The system processes data in the following order:

1. **Product Fetching** (`data_fetcher.py`):
   - Fetches 500+ products from Shopify using various search terms
   - Saves to `data/products.json`

2. **Embedding Generation**:
   - Creates text embeddings for product titles and descriptions
   - Stores in Qdrant vector database

3. **Interaction Simulation**:
   - Generates mock user interactions (views, cart adds, purchases)
   - Saves to `data/interactions.json`

4. **Collaborative Filtering**:
   - Creates co-occurrence matrix from interactions
   - Calculates lift scores for product pairs
   - Saves to `data/co_occurrence.json` and `data/lift_scores.json`

5. **Recommendation Generation**:
   - Runs hybrid algorithm on all products
   - Saves results to `data/recommendations.json`

## Algorithm Details

The hybrid recommendation system works as follows:

### 1. Candidate Generation
- **Collaborative Candidates**: Products with high lift scores relative to target
- **Content Candidates**: Products with similar embeddings to target
- **Enrichment Candidates**: Products similar to collaborative candidates

### 2. Scoring Formula
```
Final Score = w₁ × Lift(A,B) + w₂ × Similarity(A,B) + w₃ × Max_Enrichment(B)
```

Where:
- `w₁ = 0.4` (collaborative weight)
- `w₂ = 0.4` (content weight)  
- `w₃ = 0.2` (enrichment weight)

### 3. Lift Score Calculation
```
Lift(A,B) = P(A,B) / (P(A) × P(B))
```

## API Endpoints

- `GET /` - Health check
- `GET /products` - List all products
- `GET /products/{id}` - Get specific product
- `GET /recommendations/{id}` - Get recommendations for product
- `GET /recommendations` - Get all precomputed recommendations
- `GET /stats` - System statistics
- `POST /generate-recommendations` - Regenerate all recommendations

## Frontend Features

- **Product Browser**: Select any product to see recommendations
- **Score Breakdown**: Visual charts showing collaborative vs content contributions
- **Interaction Counts**: Shows how many users co-purchased items
- **System Statistics**: Monitor data pipeline and Qdrant status

## Configuration

Key configuration options in `backend/config.py`:

```python
COLLABORATIVE_WEIGHT = 0.4      # Weight for lift scores
CONTENT_WEIGHT = 0.4           # Weight for similarity scores  
ENRICHMENT_WEIGHT = 0.2        # Weight for enrichment scores
TOP_N_RECOMMENDATIONS = 5       # Number of final recommendations
TOP_K_SIMILAR = 10             # Candidates from each method
```

## Performance Notes

- **Data Collection**: ~5-10 minutes for 500 products
- **Embedding Generation**: ~10-15 minutes with OpenAI API
- **Recommendation Generation**: ~2-3 minutes for all products
- **Vector Search**: Sub-second response times with Qdrant

## Limitations

This is a prototype with several simplifications:

- Mock interaction data instead of real user behavior
- Limited to text embeddings (no image embeddings)
- Simple lift score calculation
- No real-time recommendation updates
- Basic collaborative filtering (no matrix factorization)

## Troubleshooting

1. **OpenAI API Errors**: Check API key and rate limits
2. **Qdrant Connection**: Ensure Qdrant is running on port 6333
3. **Shopify MCP Errors**: Verify store URL and MCP endpoint
4. **Empty Recommendations**: Run data pipeline in correct order
5. **Frontend Errors**: Check backend is running on port 8000
