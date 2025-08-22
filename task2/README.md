# Shopify Conversational Agent

A multi-turn chatbot that enables customers to search for products and manage their cart through natural conversation, powered by OpenAI GPT-4 and LangChain tools with Shopify Storefront API.

## Features

- **LangChain Tool-Based Architecture**: Automatic tool calling for product search, cart management, and more
- **Conversational Product Search**: Natural language product discovery with intelligent tool selection
- **Multi-turn Conversations**: Context-aware conversations that remember user preferences
- **Cart Management**: Add/remove items, view cart contents through chat
- **Smart Recommendations**: LLM-powered product suggestions and alternatives
- **Real-time Inventory**: Live product availability and stock warnings
- **Responsive UI**: Modern Streamlit interface with real-time chat

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Shopify       │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   Storefront    │
│                 │    │                 │    │   MCP           │
│   • Chat UI     │    │   • LangChain   │    │   • Products    │
│   • Product     │    │   • Tools       │    │   • Cart        │
│   • Cart View   │    │   • Agent       │    │   • Search      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## LangChain Tools

The conversation engine uses LangChain tools for automatic function calling:

- **search_products**: Find products in the store catalog
- **create_cart**: Create a new shopping cart
- **add_to_cart**: Add products to the user's cart
- **view_cart**: Display cart contents and total
- **remove_from_cart**: Remove items from cart
- **get_product_details**: Get detailed product information

The LLM automatically selects and calls the appropriate tools based on user intent.

## Quick Start

### Prerequisites

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Shopify Store URL**: Any public Shopify store (no tokens required!)

### Environment Setup

1. Clone and navigate to the project:
```bash
cd task2
```

2. Create a `.env` file:
```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Shopify Configuration
SHOPIFY_STORE_URL=amirtest100.myshopify.com
```

**Note**: The application connects directly to Shopify's built-in MCP endpoint at `https://your-store.myshopify.com/api/mcp` to get real data from the store.

### Running with Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Access the application
open http://localhost:8501
```

### Running Locally

#### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
```

#### Frontend
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

## API Key Setup Guide

### 1. OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the key and add to your `.env` file as `OPENAI_API_KEY`

### 2. Shopify MCP Integration

The application connects directly to Shopify's built-in MCP endpoint as described in the [Shopify Storefront MCP documentation](https://shopify.dev/docs/apps/build/storefront-mcp/servers/storefront).

**How it works:**
- Each Shopify store has its own MCP endpoint: `https://store-domain.myshopify.com/api/mcp`
- No additional MCP server setup required
- Direct connection to real Shopify store data

**Available MCP Tools:**
- `search_shop_catalog`: Search products in the store catalog
- `get_cart`: Retrieve cart contents and checkout URL
- `update_cart`: Add/remove items, create new carts
- `search_shop_policies_and_faqs`: Get store policies and FAQ information

**Real Data Only**: This implementation gets live data directly from Shopify stores via their built-in MCP endpoints.

## Search Workflow Sub-steps

Our search workflow follows a sophisticated multi-step process:

### 1. Intent Classification
```
User Input → LLM Analysis → Intent + Confidence + Slots
```
- **Intent types**: search, add_to_cart, remove_from_cart, view_cart, general
- **Slot extraction**: product_type, color, size, brand, price_range
- **Confidence scoring**: 0.0-1.0 for fallback handling

### 2. Slot Filling Strategy
```
Missing Slots → Clarifying Questions → User Response → Slot Updates
```
- **Required slots**: product_type (minimum for search)
- **Optional slots**: color, size, brand, price_range
- **Progressive disclosure**: Ask for most important missing slots first
- **Context awareness**: Remember previous conversation context

### 3. Query Construction
```
Slots + Context → Search Query → Shopify GraphQL
```
- **Query building**: Combine slot values into search string
- **Query optimization**: Weight important terms, handle synonyms
- **Fallback terms**: Extract keywords from natural language if slots empty

### 4. Result Filtering & Ranking
```
Raw Results → Availability Filter → Relevance Ranking → User Preferences
```
- **Availability filtering**: Prioritize in-stock items
- **Relevance scoring**: Match against user's specified criteria
- **Result limiting**: Return 5-10 most relevant products
- **Variant selection**: Choose best variant per product

### 5. Response Generation
```
Filtered Results → LLM Prompt → Natural Response → User Display
```
- **Few results (1-3)**: Show detailed product info, ask for confirmation
- **Many results (4-10)**: Show summary list, ask for selection
- **Too many results (10+)**: Ask for more specific criteria
- **No results**: Suggest alternative search terms

### 6. Conversation Flow Management
```
Current State + User Response → Next State + Actions
```
- **States**: initial → searching → clarifying → confirming → cart_management
- **Context preservation**: Maintain search results, user preferences
- **Error recovery**: Handle unclear responses, technical failures

## Example Conversation Flow

```
1. User: "I want a shirt"
   → Tool: search_products("shirt")
   → Response: "I found 5 shirts. Which one interests you?"

2. User: "Show me red shirts"
   → Tool: search_products("red shirt")
   → Response: "I found 3 red shirts. Here are the details..."

3. User: "Add the first one to my cart"
   → Tool: add_to_cart(product_id="gid://shopify/Product/123")
   → Response: "Perfect! I've added the red shirt to your cart."

4. User: "What's in my cart?"
   → Tool: view_cart()
   → Response: "Here's what's in your cart: Red Shirt - $29.99"

5. User: "Remove the shirt"
   → Tool: remove_from_cart(line_item_id="gid://shopify/CartLine/456")
   → Response: "I've removed the shirt from your cart."
```

## How LangChain Tools Work

The conversation engine automatically:

1. **Analyzes user intent** using the LLM
2. **Selects appropriate tools** based on the user's request
3. **Calls tools with parameters** extracted from the conversation
4. **Formats responses** in a natural, conversational way
5. **Maintains context** across the conversation

This approach eliminates the need for manual intent classification and provides more flexible, natural interactions.

## API Endpoints

### Chat Endpoints
- `POST /chat` - Main conversation endpoint
- `GET /conversation/{session_id}` - Get conversation history
- `DELETE /conversation/{session_id}` - Clear conversation

### Product Endpoints
- `POST /search` - Direct product search
- `GET /health` - Service health check

### Cart Endpoints
- `POST /cart/create` - Create new cart
- `POST /cart/add` - Add item to cart
- `DELETE /cart/{cart_id}/line/{line_id}` - Remove item
- `GET /cart/{cart_id}` - Get cart contents

## Configuration

Key configuration options in `backend/config.py`:

```python
# LLM Configuration
DEFAULT_MODEL = "gpt-4o-mini"
MAX_TOKENS = 1000
TEMPERATURE = 0.7

# Conversation Configuration
MAX_CONVERSATION_HISTORY = 20
SEARCH_RESULTS_LIMIT = 10
```

## Deployment Notes

### Production Considerations
1. **Environment Variables**: Store sensitive keys securely
2. **Rate Limiting**: Implement API rate limits for OpenAI calls
3. **Caching**: Cache product searches and conversation contexts
4. **Monitoring**: Track conversation success rates and user satisfaction
5. **Error Handling**: Comprehensive logging and error recovery

### Scaling Options
- **Session Storage**: Move to Redis for conversation state
- **Database**: Add PostgreSQL for conversation history
- **Load Balancing**: Use multiple backend instances
- **CDN**: Cache static assets and product images

## Troubleshooting

### Common Issues

1. **Backend not connecting**: Check OpenAI API key and Shopify store URL
2. **No products found**: Verify Shopify store has published products
3. **Cart errors**: Ensure Storefront API permissions are correct
4. **Slow responses**: Check OpenAI API quotas and latency

### Debug Mode
Set environment variable for detailed logging:
```bash
export LOG_LEVEL=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test with the provided conversation examples
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.