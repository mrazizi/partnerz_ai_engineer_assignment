#!/bin/bash

# Quick start script for Shopify Conversational Agent

echo "🛍️ Shopify Conversational Agent Setup"
echo "======================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Please create a .env file based on env.example:"
    echo "   cp env.example .env"
    echo "   # Then edit .env with your API keys"
    exit 1
fi

echo "✅ .env file found"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found! Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose not found! Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker found"

# Build and start services
echo "🔨 Building and starting services..."

# Use docker-compose or docker compose based on what's available
if command -v docker-compose &> /dev/null; then
    docker-compose up --build -d
else
    docker compose up --build -d
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Services started successfully!"
    echo ""
    echo "📱 Frontend: http://localhost:8501"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "📊 Check logs with:"
    if command -v docker-compose &> /dev/null; then
        echo "   docker-compose logs -f"
    else
        echo "   docker compose logs -f"
    fi
    echo ""
    echo "🛑 Stop services with:"
    if command -v docker-compose &> /dev/null; then
        echo "   docker-compose down"
    else
        echo "   docker compose down"
    fi
else
    echo "❌ Failed to start services. Check the logs for more information."
    exit 1
fi
