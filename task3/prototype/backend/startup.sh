#!/bin/bash

# Startup script for the recommendation system backend
echo "🚀 Starting Recommendation System Backend..."

# Check if data files exist
if [ ! -f "data/products.json" ]; then
    echo "📦 Data files not found. Running data pipeline..."
    
    # Run the data pipeline
    python data_fetcher.py
    python recommendation_engine.py
    
    echo "✅ Data pipeline completed!"
else
    echo "✅ Data files found. Skipping data pipeline."
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
