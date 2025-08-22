"""Conversation engine for handling multi-turn chatbot interactions."""
import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import openai
from shopify_client import ShopifyStorefrontClient, Product
from config import OPENAI_API_KEY, DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """States for conversation flow."""
    INITIAL = "initial"
    SEARCHING = "searching"
    CLARIFYING = "clarifying"
    CONFIRMING = "confirming"
    CART_MANAGEMENT = "cart_management"
    COMPLETED = "completed"


@dataclass
class UserIntent:
    """User intent classification."""
    intent_type: str  # search, add_to_cart, remove_from_cart, view_cart, general
    confidence: float
    slots: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Context for maintaining conversation state."""
    state: ConversationState = ConversationState.INITIAL
    user_intent: Optional[UserIntent] = None
    search_query: str = ""
    search_results: List[Product] = field(default_factory=list)
    selected_products: List[Product] = field(default_factory=list)
    cart_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    pending_slots: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        # Keep only last 20 messages to avoid context length issues
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


class ConversationEngine:
    """Main conversation engine for the Shopify chatbot."""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.shopify_client = ShopifyStorefrontClient()
        self.contexts: Dict[str, ConversationContext] = {}
    
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get or create conversation context for a session."""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext()
        return self.contexts[session_id]
    
    def process_message(self, session_id: str, user_message: str) -> str:
        """Process user message and return bot response."""
        context = self.get_or_create_context(session_id)
        context.add_message("user", user_message)
        
        try:
            # Step 1: Classify user intent
            intent = self._classify_intent(user_message, context)
            context.user_intent = intent
            
            # Step 2: Process based on intent and current state
            response = self._process_intent(intent, context)
            
            # Step 3: Add bot response to history
            context.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            error_response = "I'm sorry, I encountered an error. Could you please try again?"
            context.add_message("assistant", error_response)
            return error_response
    
    def _classify_intent(self, user_message: str, context: ConversationContext) -> UserIntent:
        """Classify user intent using OpenAI."""
        system_prompt = """You are an intent classifier for a shopping chatbot. 
        Analyze the user's message and classify their intent into one of these categories:
        
        - search: User wants to find products
        - add_to_cart: User wants to add items to cart
        - remove_from_cart: User wants to remove items from cart
        - view_cart: User wants to see cart contents
        - general: General conversation, greetings, questions
        
        Also extract relevant slots:
        - product_type: shirt, shoes, etc.
        - color: red, blue, etc.
        - size: S, M, L, XL, etc.
        - brand: specific brand names
        - price_range: budget constraints
        
        Respond in JSON format:
        {
            "intent": "search|add_to_cart|remove_from_cart|view_cart|general",
            "confidence": 0.0-1.0,
            "slots": {
                "product_type": "value",
                "color": "value",
                "size": "value"
            }
        }"""
        
        # Add conversation context
        conversation_context = ""
        if context.conversation_history:
            recent_history = context.conversation_history[-6:]  # Last 3 exchanges
            conversation_context = "Previous conversation:\n"
            for msg in recent_history:
                conversation_context += f"{msg['role']}: {msg['content']}\n"
        
        user_prompt = f"{conversation_context}\nCurrent message: {user_message}"
        
        # Log the request details
        logger.info("=== INTENT CLASSIFICATION REQUEST ===")
        logger.info(f"Model: {DEFAULT_MODEL}")
        logger.info(f"System prompt: {system_prompt}")
        logger.info(f"User prompt: {user_prompt}")
        logger.info(f"Max tokens: 300")
        logger.info(f"Temperature: 0.3")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            logger.info("=== INTENT CLASSIFICATION RESPONSE ===")
            logger.info(f"Response status: Success")
            logger.info(f"Response content: {response.choices[0].message.content}")
            
            result = json.loads(response.choices[0].message.content)
            return UserIntent(
                intent_type=result.get("intent", "general"),
                confidence=result.get("confidence", 0.5),
                slots=result.get("slots", {})
            )
        except Exception as e:
            logger.error(f"=== INTENT CLASSIFICATION ERROR ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            # Fallback to simple keyword matching
            return self._fallback_intent_classification(user_message)
    
    def _fallback_intent_classification(self, user_message: str) -> UserIntent:
        """Fallback intent classification using keyword matching."""
        message_lower = user_message.lower()
        
        # Simple keyword-based classification
        if any(word in message_lower for word in ["search", "find", "looking for", "want", "need"]):
            # Extract product type
            product_keywords = ["shirt", "tee", "polo", "jacket", "pants", "jeans", "shoes", "sneakers"]
            product_type = None
            for keyword in product_keywords:
                if keyword in message_lower:
                    product_type = keyword
                    break
            
            slots = {}
            if product_type:
                slots["product_type"] = product_type
            
            return UserIntent("search", 0.7, slots)
        
        elif any(word in message_lower for word in ["add", "cart", "buy", "purchase"]):
            return UserIntent("add_to_cart", 0.7, {})
        
        elif any(word in message_lower for word in ["remove", "delete", "take out"]):
            return UserIntent("remove_from_cart", 0.7, {})
        
        elif any(word in message_lower for word in ["cart", "basket", "what's in"]):
            return UserIntent("view_cart", 0.7, {})
        
        else:
            return UserIntent("general", 0.5, {})
    
    def _process_intent(self, intent: UserIntent, context: ConversationContext) -> str:
        """Process user intent and generate appropriate response."""
        if intent.intent_type == "search":
            return self._handle_search_intent(intent, context)
        elif intent.intent_type == "add_to_cart":
            return self._handle_add_to_cart_intent(intent, context)
        elif intent.intent_type == "remove_from_cart":
            return self._handle_remove_from_cart_intent(intent, context)
        elif intent.intent_type == "view_cart":
            return self._handle_view_cart_intent(intent, context)
        else:
            return self._handle_general_intent(intent, context)
    
    def _handle_search_intent(self, intent: UserIntent, context: ConversationContext) -> str:
        """Handle product search intent."""
        # Build search query from slots
        search_terms = []
        
        if "product_type" in intent.slots:
            search_terms.append(intent.slots["product_type"])
        
        if "color" in intent.slots:
            search_terms.append(intent.slots["color"])
        
        if "size" in intent.slots:
            search_terms.append(intent.slots["size"])
        
        if "brand" in intent.slots:
            search_terms.append(intent.slots["brand"])
        
        # If no specific terms, extract from the last user message
        if not search_terms:
            last_message = context.conversation_history[-1]["content"]
            search_terms = self._extract_search_terms(last_message)
        
        search_query = " ".join(search_terms)
        context.search_query = search_query
        
        try:
            # Search for products
            products = self.shopify_client.search_products(search_query, limit=10)
            context.search_results = products
            
            if not products:
                return f"I couldn't find any products matching '{search_query}'. Could you try different keywords?"
            
            # Check if we need to clarify choices
            if len(products) > 5:
                # Too many results, ask for clarification
                context.state = ConversationState.CLARIFYING
                return self._generate_clarification_response(products, intent.slots)
            else:
                # Show results and ask for selection
                context.state = ConversationState.CONFIRMING
                return self._generate_product_list_response(products)
                
        except Exception as e:
            return "I'm having trouble searching for products right now. Please try again later."
    
    def _handle_add_to_cart_intent(self, intent: UserIntent, context: ConversationContext) -> str:
        """Handle add to cart intent."""
        # Check if we have a selected product
        if not context.selected_products:
            if context.search_results:
                return "Which product would you like to add to your cart? Please specify the product name."
            else:
                return "I don't see any products selected. Would you like to search for something first?"
        
        # Create cart if doesn't exist
        if not context.cart_id:
            try:
                context.cart_id = self.shopify_client.create_cart()
            except Exception as e:
                return "I'm having trouble creating a cart. Please try again."
        
        # Add the last selected product to cart
        product = context.selected_products[-1]
        
        # Find appropriate variant (default to first available)
        variant_to_add = None
        for variant in product.variants:
            if True:  # Default to available since we removed the field
                variant_to_add = variant
                break
        
        if not variant_to_add:
            return f"Sorry, {product.title} is currently out of stock."
        
        try:
            self.shopify_client.add_to_cart(context.cart_id, variant_to_add["id"], 1)
            return f"Great! I've added {product.title} to your cart. Is there anything else you'd like to add?"
        except Exception as e:
            return f"I had trouble adding {product.title} to your cart. Please try again."
    
    def _handle_remove_from_cart_intent(self, intent: UserIntent, context: ConversationContext) -> str:
        """Handle remove from cart intent."""
        if not context.cart_id:
            return "Your cart is empty. There's nothing to remove."
        
        try:
            cart = self.shopify_client.get_cart(context.cart_id)
            cart_lines = cart.get("lines", {}).get("edges", [])
            
            if not cart_lines:
                return "Your cart is empty. There's nothing to remove."
            
            # For now, remove the last added item
            # In a more sophisticated version, we'd parse which item to remove
            last_line = cart_lines[-1]
            line_id = last_line["node"]["id"]
            product_title = last_line["node"]["merchandise"]["product"]["title"]
            
            self.shopify_client.remove_from_cart(context.cart_id, line_id)
            return f"I've removed {product_title} from your cart."
            
        except Exception as e:
            return "I had trouble removing the item from your cart. Please try again."
    
    def _handle_view_cart_intent(self, intent: UserIntent, context: ConversationContext) -> str:
        """Handle view cart intent."""
        if not context.cart_id:
            return "Your cart is empty. Would you like to search for some products?"
        
        try:
            cart = self.shopify_client.get_cart(context.cart_id)
            cart_lines = cart.get("lines", {}).get("edges", [])
            
            if not cart_lines:
                return "Your cart is empty. Would you like to search for some products?"
            
            cart_summary = "Here's what's in your cart:\n\n"
            total = 0.0
            
            for line in cart_lines:
                node = line["node"]
                merchandise = node["merchandise"]
                product_title = merchandise["product"]["title"]
                variant_title = merchandise["title"]
                quantity = node["quantity"]
                price = float(merchandise["price"]["amount"])
                currency = merchandise["price"]["currencyCode"]
                
                line_total = price * quantity
                total += line_total
                
                cart_summary += f"• {product_title} ({variant_title}) - Qty: {quantity} - ${line_total:.2f}\n"
            
            cart_summary += f"\nTotal: ${total:.2f}"
            cart_summary += "\n\nWould you like to add more items or make any changes?"
            
            return cart_summary
            
        except Exception as e:
            return "I had trouble retrieving your cart. Please try again."
    
    def _handle_general_intent(self, intent: UserIntent, context: ConversationContext) -> str:
        """Handle general conversation intent."""
        user_message = context.conversation_history[-1]["content"]
        
        # Use LLM for general responses
        system_prompt = """You are a helpful shopping assistant for a Shopify store. 
        Be friendly, helpful, and guide users towards finding and purchasing products.
        Keep responses concise and conversational.
        If users ask about products, encourage them to search.
        If they seem lost, offer to help them find what they need."""
        
        # Log the request details
        logger.info("=== GENERAL INTENT REQUEST ===")
        logger.info(f"Model: {DEFAULT_MODEL}")
        logger.info(f"System prompt: {system_prompt}")
        logger.info(f"User message: {user_message}")
        logger.info(f"Max tokens: 200")
        logger.info(f"Temperature: 0.7")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            logger.info("=== GENERAL INTENT RESPONSE ===")
            logger.info(f"Response status: Success")
            logger.info(f"Response content: {response.choices[0].message.content}")
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"=== GENERAL INTENT ERROR ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return "Hello! I'm here to help you find great products. What are you looking for today?"
    
    def _extract_search_terms(self, message: str) -> List[str]:
        """Extract search terms from user message."""
        # Simple extraction - in production, use more sophisticated NLP
        words = re.findall(r'\b\w+\b', message.lower())
        
        # Filter out common stop words
        stop_words = {"i", "want", "need", "looking", "for", "a", "an", "the", "some", "find", "search"}
        search_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return search_terms[:3]  # Limit to 3 terms
    
    def _generate_clarification_response(self, products: List[Product], slots: Dict[str, Any]) -> str:
        """Generate response asking for clarification when too many results."""
        response = f"I found {len(products)} products. To help narrow it down, could you tell me:\n\n"
        
        # Ask for missing slots
        if "color" not in slots:
            response += "• What color would you prefer?\n"
        if "size" not in slots:
            response += "• What size do you need?\n"
        if "product_type" not in slots:
            response += "• What type of product are you looking for?\n"
        
        # Show a few example products
        response += "\nHere are some examples of what I found:\n"
        for i, product in enumerate(products[:3]):
            response += f"• {product.title} - ${product.price:.2f}\n"
        
        return response
    
    def _generate_product_list_response(self, products: List[Product]) -> str:
        """Generate response showing product list."""
        if len(products) == 1:
            product = products[0]
            response = f"I found this product: **{product.title}**\n"
            response += f"Price: ${product.price:.2f}\n"
            if product.description:
                response += f"Description: {product.description[:100]}...\n"
            response += "\nWould you like to add this to your cart?"
            return response
        
        response = "Here's what I found:\n\n"
        for i, product in enumerate(products, 1):
            response += f"{i}. **{product.title}** - ${product.price:.2f}\n"
            if product.description:
                response += f"   {product.description[:80]}...\n"
            response += "\n"
        
        response += "Which one interests you? You can tell me the number or the product name."
        return response
