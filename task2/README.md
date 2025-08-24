# Task 2: Shopify Conversational Agent

## Overview
A multi-turn conversational AI agent for Shopify stores that enables natural language product search, cart management, and shopping assistance using LangChain tools and Shopify's MCP (Model Context Protocol) integration.

## Technologies Used

### Backend
- **FastAPI**: RESTful API framework for conversational endpoints
- **LangChain**: Conversational AI orchestration with tools and agents
- **OpenAI**: GPT-4o for natural language understanding and generation
- **Shopify MCP**: Model Context Protocol for direct store integration
- **Pydantic**: Data validation and request/response models

### Frontend
- **Streamlit**: Interactive chat interface with real-time messaging
- **Requests**: HTTP client for backend communication
- **Session Management**: Conversation state persistence

### Infrastructure
- **Docker & Docker Compose**: Containerization and service orchestration

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Shopify       │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   MCP Server    │
│   Port: 8501    │    │   Port: 8000    │    │   (Store API)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (GPT-4o)      │
                       └─────────────────┘
```

## Workflow

### 1. Conversation Flow
```
User Input → Frontend → Backend → LangChain Agent → Tool Selection → Shopify MCP → Response
```

### 2. Multi-Turn Dialogue
1. **User Message**: Natural language query via Streamlit chat
2. **Context Management**: Session-based conversation history
3. **Tool Selection**: LangChain agent chooses appropriate tools
4. **Shopify Integration**: MCP server executes store operations
5. **Response Generation**: GPT-4o formulates natural response
6. **State Update**: Conversation context maintained for continuity

### 3. Available Tools
- **Product Search**: `search_shop_catalog` - Find products by query
- **Cart Management**: `add_to_cart`, `remove_from_cart` - Cart operations
- **Product Details**: `get_product_details` - Retrieve specific product info
- **Store Info**: `get_shop_info` - Store metadata and collections

## Design Components

### Backend Services
- **ConversationEngine**: LangChain agent with tool integration
- **ShopifyStorefrontClient**: MCP client for store operations
- **Session Management**: Conversation context and state tracking
- **FastAPI Endpoints**: `/chat`, `/tools/list`, `/health`

### Frontend Features
- **Real-time Chat Interface**: Message streaming and typing indicators
- **Session Persistence**: Conversation history across page reloads
- **Product Display**: Rich product cards with images and details
- **Cart Visualization**: Real-time cart status and item management
- **System Status**: Backend connectivity and tool availability

### LangChain Integration
- **Agent Type**: OpenAI Tools Agent
- **Tool Framework**: Custom Shopify MCP tools
- **Memory**: Conversation history with context window management
- **Error Handling**: Graceful fallbacks and parsing error recovery

## How to Run

```bash
cd task2
docker-compose up -d --build
```

Access the application at:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000

## Key Features
- ✅ Natural language product search
- ✅ Multi-turn conversation support
- ✅ Cart management (add/remove items)
- ✅ Session-based conversation history
- ✅ Real-time chat interface
- ✅ Shopify MCP integration
- ✅ LangChain tool orchestration
- ✅ Docker containerization
