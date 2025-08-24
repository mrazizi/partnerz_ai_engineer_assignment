"""Conversation engine for handling multi-turn chatbot interactions using LangChain tools."""
import json
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from shopify_client import ShopifyStorefrontClient, Product
from config import OPENAI_API_KEY, DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for maintaining conversation state."""
    search_query: str = ""
    search_results: List[Product] = field(default_factory=list)
    selected_products: List[Product] = field(default_factory=list)
    cart_id: Optional[str] = None
    conversation_history: List[BaseMessage] = field(default_factory=list)
    pending_slots: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: BaseMessage):
        """Add message to conversation history."""
        self.conversation_history.append(message)
        # Keep only last 20 messages to avoid context length issues
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


class ConversationEngine:
    """Main conversation engine for the Shopify chatbot using LangChain tools."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            openai_api_key=OPENAI_API_KEY
        )
        self.shopify_client = ShopifyStorefrontClient()
        self.contexts: Dict[str, ConversationContext] = {}
        
        self.tools = self._create_tools()
        
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _create_tools(self) -> List:
        """Create LangChain tools for the conversation engine."""
        
        @tool
        def search_products(query: str, limit: int = 10) -> str:
            """Search for products in the store. Use this when users want to find products.
            
            Args:
                query: The search query (e.g., "red shirt", "shoes", "jeans")
                limit: Maximum number of products to return (default: 10)
            
            Returns:
                A formatted string with product information
            """
            try:
                logger.info(f"=== SEARCH PRODUCTS TOOL ===")
                logger.info(f"Query: {query}")
                logger.info(f"Limit: {limit}")
                
                products = self.shopify_client.search_products(query, limit)
                
                if not products:
                    return f"I couldn't find any products matching '{query}'. Could you try different keywords?"
                
                # Format the response
                if len(products) == 1:
                    product = products[0]
                    response = f"I found this product: **{product.title}**\n"
                    response += f"Price: ${product.price:.2f}\n"
                    if product.description:
                        response += f"Description: {product.description[:100]}...\n"
                    response += f"Product ID: {product.id}\n"
                    response += "\nWould you like to add this to your cart?"
                else:
                    response = f"I found {len(products)} products:\n\n"
                    for i, product in enumerate(products, 1):
                        response += f"{i}. **{product.title}** - ${product.price:.2f}\n"
                        if product.description:
                            response += f"   {product.description[:80]}...\n"
                        response += f"   Product ID: {product.id}\n\n"
                    
                    response += "Which one interests you? You can tell me the product name or ID."
                
                context = self._get_current_context()
                context.search_results = products
                context.search_query = query
                
                logger.info(f"Search results: {len(products)} products found")
                return response
                
            except Exception as e:
                logger.error(f"Search products error: {str(e)}")
                return "I'm having trouble searching for products right now. Please try again later."
        
        @tool
        def create_cart() -> str:
            """Create a new shopping cart. Use this when users want to start shopping."""
            try:
                logger.info("=== CREATE CART TOOL ===")
                
                cart_id = self.shopify_client.create_cart()
                if cart_id:
                    logger.info(f"Cart created with ID: {cart_id}")
                    return f"Great! I've created a new shopping cart for you. Your cart ID is: {cart_id}"
                else:
                    return "I'm having trouble creating a cart. Please try again."
                    
            except Exception as e:
                logger.error(f"Create cart error: {str(e)}")
                return "I'm having trouble creating a cart. Please try again."
        
        @tool
        def add_to_cart(product_reference: str, quantity: int = 1) -> str:
            """Add a product to the user's cart. Use this when users want to buy something.
            
            Args:
                product_reference: Can be a product number from search results (e.g., "3"), product ID, or variant ID
                quantity: How many to add (default: 1)
            """
            try:
                logger.info(f"=== ADD TO CART TOOL ===")
                logger.info(f"Product Reference: {product_reference}")
                logger.info(f"Quantity: {quantity}")
                
                context = self._get_current_context()
                if not context.cart_id:
                    cart_id = self.shopify_client.create_cart()
                    if cart_id:
                        context.cart_id = cart_id
                    else:
                        return "I'm having trouble creating a cart. Please try again."
                else:
                    cart_id = context.cart_id
                
                # Resolve product reference to variant ID
                variant_id = self._resolve_product_reference(product_reference, context)
                if not variant_id:
                    return f"I couldn't find a product matching '{product_reference}'. Could you try again with a product name, number from the search results, or product ID?"
                
                logger.info(f"Resolved to variant ID: {variant_id}")
                
                result = self.shopify_client.add_to_cart(cart_id, variant_id, quantity)
                
                logger.info(f"Added to cart successfully")
                return f"Perfect! I've added the product to your cart. Is there anything else you'd like to add?"
                
            except Exception as e:
                logger.error(f"Add to cart error: {str(e)}")
                return f"I had trouble adding the product to your cart. Please try again."
        
        @tool
        def view_cart() -> str:
            """View the contents of the user's cart. Use this when users want to see what's in their cart."""
            try:
                logger.info("=== VIEW CART TOOL ===")
                
                context = self._get_current_context()
                if not context.cart_id:
                    return "Your cart is empty. Would you like to search for some products?"
                
                cart = self.shopify_client.get_cart(context.cart_id)
                
                cart_lines = []
                if "lines" in cart:
                    if isinstance(cart["lines"], dict) and "edges" in cart["lines"]:
                        cart_lines = cart["lines"]["edges"]
                    elif isinstance(cart["lines"], list):
                        cart_lines = cart["lines"]
                
                if not cart_lines:
                    return "Your cart is empty. Would you like to search for some products?"
                
                cart_summary = "Here's what's in your cart:\n\n"
                total = 0.0
                
                for line in cart_lines:
                    if isinstance(line, dict) and "node" in line:
                        node = line["node"]
                        merchandise = node.get("merchandise", {})
                        product_title = merchandise.get("product", {}).get("title", "Unknown Product")
                        variant_title = merchandise.get("title", "")
                        quantity = node.get("quantity", 1)
                        price_data = merchandise.get("price", {})
                        price = float(price_data.get("amount", 0))
                        currency = price_data.get("currencyCode", "USD")
                    else:
                        merchandise = line.get("merchandise", {})
                        product_title = merchandise.get("product", {}).get("title", "Unknown Product")
                        variant_title = merchandise.get("title", "")
                        quantity = line.get("quantity", 1)
                        price_data = merchandise.get("price", {})
                        price = float(price_data.get("amount", 0))
                        currency = price_data.get("currencyCode", "USD")
                    
                    line_total = price * quantity
                    total += line_total
                    
                    cart_summary += f"• {product_title} ({variant_title}) - Qty: {quantity} - ${line_total:.2f}\n"
                
                cart_summary += f"\nTotal: ${total:.2f}"
                cart_summary += "\n\nWould you like to add more items or make any changes?"
                
                logger.info(f"Cart viewed successfully")
                return cart_summary
                
            except Exception as e:
                logger.error(f"View cart error: {str(e)}")
                return "I had trouble retrieving your cart. Please try again."
        
        @tool
        def remove_from_cart(line_item_id: str) -> str:
            """Remove an item from the user's cart. Use this when users want to remove something.
            
            Args:
                line_item_id: The ID of the line item to remove
            """
            try:
                logger.info(f"=== REMOVE FROM CART TOOL ===")
                logger.info(f"Line item ID: {line_item_id}")
                
                context = self._get_current_context()
                if not context.cart_id:
                    return "Your cart is empty. There's nothing to remove."
                
                self.shopify_client.remove_from_cart(context.cart_id, line_item_id)
                
                logger.info(f"Item removed from cart successfully")
                return "I've removed the item from your cart."
                
            except Exception as e:
                logger.error(f"Remove from cart error: {str(e)}")
                return "I had trouble removing the item from your cart. Please try again."
        
        @tool
        def get_product_details(product_id: str) -> str:
            """Get detailed information about a specific product. Use this when users want to know more about a product.
            
            Args:
                product_id: The product ID to get details for
            """
            try:
                logger.info(f"=== GET PRODUCT DETAILS TOOL ===")
                logger.info(f"Product ID: {product_id}")
                
                product = self.shopify_client.get_product_by_id(product_id)
                
                if not product:
                    return f"I couldn't find a product with ID {product_id}."
                
                response = f"**{product.title}**\n"
                response += f"Price: ${product.price:.2f}\n"
                if product.description:
                    response += f"Description: {product.description}\n"
                response += f"Product ID: {product.id}\n"
                
                if product.variants:
                    response += "\nAvailable variants:\n"
                    for variant in product.variants:
                        response += f"• {variant['title']} - ${variant['price']:.2f} (ID: {variant['id']})\n"
                
                logger.info(f"Product details retrieved successfully")
                return response
                
            except Exception as e:
                logger.error(f"Get product details error: {str(e)}")
                return "I'm having trouble getting product details. Please try again."
        
        return [
            search_products,
            create_cart,
            add_to_cart,
            view_cart,
            remove_from_cart,
            get_product_details
        ]
    
    def _create_agent(self):
        """Create the LangChain agent with tools."""
        
        system_prompt = """You are a helpful shopping assistant for a Shopify store. 
        
        Your job is to help customers find products, manage their cart, and have a great shopping experience.
        
        Guidelines:
        - Be friendly, helpful, and conversational
        - When users want to find products, use the search_products tool
        - When users want to add items to cart, use the add_to_cart tool with the correct product reference
        - When users want to see their cart, use the view_cart tool
        - When users want to remove items, use the remove_from_cart tool
        - When users want product details, use the get_product_details tool
        - Keep responses concise and helpful
        - If users seem lost, offer to help them search for products
        - Always provide clear next steps for users
        
        IMPORTANT: When users reference products for adding to cart:
        - If they say "number 3" or "product 3", use "3" as the product_reference
        - If they mention a product name (like "Ocean Blue Shirt"), use the product name
        - If they provide a Shopify ID, use that ID directly
        - The add_to_cart tool will automatically resolve these references to the correct variant IDs
        - The system uses Shopify's MCP update_cart tool with add_items format
        
        Available tools:
        - search_products: Find products in the store
        - create_cart: Create a new shopping cart
        - add_to_cart: Add products to cart (handles product numbers, names, or IDs)
        - view_cart: See what's in the cart
        - remove_from_cart: Remove items from cart
        - get_product_details: Get detailed product information
        
        Remember: Always use the appropriate tool when users want to perform actions, and provide helpful responses."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return create_openai_tools_agent(self.llm, self.tools, prompt)
    
    def _resolve_product_reference(self, product_reference: str, context: ConversationContext) -> Optional[str]:
        """Resolve a product reference to a variant ID.
        
        Args:
            product_reference: Can be a number (from search results), product ID, or variant ID
            context: Current conversation context with search results
            
        Returns:
            Variant ID that can be used for cart operations, or None if not found
        """
        try:
            # Check if it's a number referring to search results
            if product_reference.isdigit():
                product_index = int(product_reference) - 1  # Convert to 0-based index
                if 0 <= product_index < len(context.search_results):
                    product = context.search_results[product_index]
                    # Get the first available variant ID
                    if product.variants and len(product.variants) > 0:
                        return product.variants[0]['id']
                    else:
                        # Fallback: try to get variant by searching for the product
                        detailed_product = self.shopify_client.get_product_by_id(product.id)
                        if detailed_product and detailed_product.variants:
                            return detailed_product.variants[0]['id']
                return None
            
            # Check if it's already a variant ID (starts with gid://shopify/ProductVariant/)
            if product_reference.startswith("gid://shopify/ProductVariant/"):
                return product_reference
            
            # Check if it's a product ID (starts with gid://shopify/Product/)
            if product_reference.startswith("gid://shopify/Product/"):
                # Get product details to find variants
                detailed_product = self.shopify_client.get_product_by_id(product_reference)
                if detailed_product and detailed_product.variants:
                    return detailed_product.variants[0]['id']
                return None
            
            # Try to search by product name/title from current search results
            for product in context.search_results:
                if product_reference.lower() in product.title.lower():
                    if product.variants and len(product.variants) > 0:
                        return product.variants[0]['id']
                    else:
                        # Fallback: get product details
                        detailed_product = self.shopify_client.get_product_by_id(product.id)
                        if detailed_product and detailed_product.variants:
                            return detailed_product.variants[0]['id']
            
            # If nothing found, try searching for the product
            products = self.shopify_client.search_products(product_reference, limit=1)
            if products and len(products) > 0:
                product = products[0]
                if product.variants and len(product.variants) > 0:
                    return product.variants[0]['id']
                else:
                    # Get detailed product info
                    detailed_product = self.shopify_client.get_product_by_id(product.id)
                    if detailed_product and detailed_product.variants:
                        return detailed_product.variants[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving product reference '{product_reference}': {str(e)}")
            return None
    
    def _get_current_context(self) -> ConversationContext:
        """Get the current conversation context (for tools to access)."""
        if not hasattr(self, '_current_session_id'):
            return ConversationContext()
        
        return self.get_or_create_context(self._current_session_id)
    
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get or create conversation context for a session."""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext()
        return self.contexts[session_id]
    
    def process_message(self, session_id: str, user_message: str) -> str:
        """Process user message and return bot response using LangChain tools."""
        context = self.get_or_create_context(session_id)
        context.add_message(HumanMessage(content=user_message))
        
        # Set current session for tools to access
        self._current_session_id = session_id
        
        try:
            chat_history = context.conversation_history[:-1]  # Exclude the current message
            
            result = self.agent_executor.invoke({
                "input": user_message,
                "chat_history": chat_history
            })
            
            response = result["output"]
            
            context.add_message(AIMessage(content=response))
            
            return response
            
        except Exception as e:
            logger.error(f"=== PROCESSING ERROR ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            
            error_response = "I'm sorry, I encountered an error. Could you please try again?"
            context.add_message(AIMessage(content=error_response))
            return error_response
