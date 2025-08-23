"""Main FastAPI application for Shopify Conversational Agent."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from conversation_engine import ConversationEngine
from shopify_client import ShopifyStorefrontClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Shopify Conversational Agent",
    description="A multi-turn chatbot for Shopify product search and cart management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize conversation engine
conversation_engine = ConversationEngine()
shopify_client = ShopifyStorefrontClient()


class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str


class ProductSearchRequest(BaseModel):
    """Product search request model."""
    query: str
    limit: int = 10


class CartRequest(BaseModel):
    """Cart management request model."""
    cart_id: Optional[str] = None
    variant_id: Optional[str] = None
    quantity: int = 1


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Shopify connection using tokenless access
        products = shopify_client.search_products("test", limit=1)
        return {
            "status": "healthy",
            "shopify_connection": "connected",
            "access_type": "mcp",
            "message": "Shopify Conversational Agent using MCP with fallback"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "shopify_connection": "disconnected",
            "access_type": "mcp",
            "error": str(e)
        }


@app.get("/tools/list")
async def list_mcp_tools():
    """List available tools from Shopify Storefront MCP server."""
    try:
        # Make MCP tools/list request
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        import requests
        response = requests.post(
            shopify_client.mcp_endpoint,
            headers=shopify_client.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            raise Exception(f"MCP server error: {result['error']}")
        
        tools = result.get("result", {}).get("tools", [])
        
        return {
            "success": True,
            "tools": tools,
            "count": len(tools),
            "mcp_endpoint": shopify_client.mcp_endpoint
        }
        
    except Exception as e:
        logger.error(f"List tools error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "mcp_endpoint": shopify_client.mcp_endpoint
        }


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Main chat endpoint for conversational interactions."""
    try:
        # Generate session ID if not provided
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        logger.info(f"=== CHAT REQUEST ===")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"User message: {chat_message.message}")
        
        # Process the message through conversation engine
        response = conversation_engine.process_message(session_id, chat_message.message)
        
        logger.info(f"=== CHAT RESPONSE ===")
        logger.info(f"Bot response: {response}")
        
        return ChatResponse(
            response=response,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"=== CHAT ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during chat processing")


@app.post("/search")
async def search_products(request: ProductSearchRequest):
    """Search for products."""
    try:
        products = shopify_client.search_products(request.query, request.limit)
        
        # Convert products to serializable format
        product_list = []
        for product in products:
            product_data = {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "handle": product.handle,
                "price": product.price,
                "currency": product.currency,
                "available": True,  # Default to available since we removed the field
                "vendor": "",  # Vendor field not available in MCP response
                "product_type": "",  # Product type field not available in MCP response
                "tags": [],  # Tags field not available in MCP response
                "variants": product.variants,
                "images": product.images
            }
            product_list.append(product_data)
        
        return {
            "products": product_list,
            "count": len(product_list),
            "query": request.query
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/cart/create")
async def create_cart():
    """Create a new shopping cart."""
    try:
        cart_id = shopify_client.create_cart()
        if cart_id is None:
            raise Exception("Failed to create cart - no cart_id returned from Shopify MCP")
        return {"cart_id": cart_id}
        
    except Exception as e:
        logger.error(f"Cart creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cart creation failed: {str(e)}")


@app.post("/cart/add")
async def add_to_cart(request: CartRequest):
    """Add item to cart."""
    try:
        if not request.cart_id:
            raise HTTPException(status_code=400, detail="Cart ID is required")
        if not request.variant_id:
            raise HTTPException(status_code=400, detail="Variant ID is required")
        
        cart = shopify_client.add_to_cart(
            request.cart_id, 
            request.variant_id, 
            request.quantity
        )
        
        return {"success": True, "cart": cart}
        
    except Exception as e:
        logger.error(f"Add to cart error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Add to cart failed: {str(e)}")


@app.delete("/cart/{cart_id}/line/{line_id}")
async def remove_from_cart(cart_id: str, line_id: str):
    """Remove item from cart."""
    try:
        cart = shopify_client.remove_from_cart(cart_id, line_id)
        return {"success": True, "cart": cart}
        
    except Exception as e:
        logger.error(f"Remove from cart error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Remove from cart failed: {str(e)}")


@app.get("/cart/{cart_id:path}")
async def get_cart(cart_id: str):
    """Get cart contents."""
    try:
        # Decode URL-encoded cart_id
        import urllib.parse
        decoded_cart_id = urllib.parse.unquote(cart_id)
        
        cart = shopify_client.get_cart(decoded_cart_id)
        return {"cart": cart}
        
    except Exception as e:
        logger.error(f"Get cart error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get cart failed: {str(e)}")


@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session."""
    try:
        context = conversation_engine.get_or_create_context(session_id)
        
        # Convert LangChain messages to simple format for API response
        conversation_history = []
        for message in context.conversation_history:
            if hasattr(message, 'content'):
                conversation_history.append({
                    "role": "user" if hasattr(message, 'type') and message.type == "human" else "assistant",
                    "content": message.content
                })
        
        return {
            "session_id": session_id,
            "conversation_history": conversation_history,
            "cart_id": context.cart_id
        }
        
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get conversation failed: {str(e)}")


@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session."""
    try:
        if session_id in conversation_engine.contexts:
            del conversation_engine.contexts[session_id]
        
        return {"success": True, "message": "Conversation cleared"}
        
    except Exception as e:
        logger.error(f"Clear conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Clear conversation failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Shopify Conversational Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
