"""Shopify Storefront MCP client for product search and cart management.

Uses the Storefront MCP server to get real data from Shopify stores.
The MCP server provides a standardized interface for storefront operations.
"""
import json
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from config import SHOPIFY_STORE_URL


@dataclass
class Product:
    """Product data model for Shopify MCP access."""
    id: str
    title: str
    description: str
    handle: str
    price: float
    currency: str
    variants: List[Dict[str, Any]]
    images: str


@dataclass
class CartItem:
    """Cart item data model."""
    variant_id: str
    product_id: str
    title: str
    price: float
    quantity: int
    size: str = ""
    color: str = ""


class ShopifyStorefrontClient:
    """Shopify Storefront MCP client using MCP server.
    
    This client connects to a Storefront MCP server for:
    - Product search and discovery
    - Cart management (add/remove items)
    - Store information and collections
    - Inventory and availability checks
    """
    
    def __init__(self):
        self.store_url = SHOPIFY_STORE_URL
        # Shopify's built-in MCP server endpoint for this store
        self.mcp_endpoint = f"https://{self.store_url}/api/mcp"
        
        # Standard MCP headers
        self.headers = {
            "Content-Type": "application/json"
        }
        print(f"Using Shopify MCP endpoint: {self.mcp_endpoint}")
    
    def _make_mcp_tool_request(self, tool_name: str, arguments: Dict = None) -> Dict[str, Any]:
        """Make MCP tool request to Shopify's built-in MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        try:
            response = requests.post(
                self.mcp_endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP server error: {result['error']}")
            
            return result.get("result", {})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"MCP server connection failed: {str(e)}")
    

    
    def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Search for products using Shopify's Storefront MCP server."""
        
        # Use the search_shop_catalog tool as per Shopify MCP documentation
        tool_name = "search_shop_catalog"
        arguments = {
            "query": query,
            "context": f"Customer searching for {query}"
        }
        
        response = self._make_mcp_tool_request(tool_name, arguments)
        response_products = json.loads(response["content"][0]["text"])["products"]
        

        # print("==============================================")
        # print(type(response_products))
        # print(response_products)
        # print("==============================================")

        products = []

        for product_data in response_products:
            # Extract variants
            variants = []
            for variant_data in product_data.get("variants", []):
                # Handle price from variant's price_range if available
                if "price_range" in variant_data:
                    variant_price = float(variant_data["price_range"].get("min", "0.00"))
                    variant_currency = variant_data["price_range"].get("currency", "USD")
                else:
                    variant_price = float(variant_data.get("price", "0.00"))
                    variant_currency = variant_data.get("currency", "USD")
                
                variant = {
                    "id": variant_data["variant_id"],
                    "title": variant_data["title"],
                    "available": variant_data.get("available", True),  # Default to True if not present
                    "price": variant_price,
                    "currency": variant_currency,
                    "image_url": variant_data.get("image_url", "")
                }
                variants.append(variant)
            
            # Extract images
            image_url = product_data.get("image_url", [])
            
            # Extract price from price_range
            price_range = product_data.get("price_range", {})
            price = float(price_range.get("min", "0.00"))
            currency = price_range.get("currency", "USD")
            
            product = Product(
                id=product_data["product_id"],
                title=product_data["title"],
                description=product_data.get("description", ""),
                handle=product_data.get("handle", ""),
                price=price,
                currency=currency,
                variants=variants,
                images=image_url
            )
            products.append(product)
        
        return products
    
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Get a specific product by ID using search (no direct get product tool in MCP)."""
        # Use search with product ID as context
        arguments = {
            "query": product_id,
            "context": f"Looking for specific product with ID: {product_id}"
        }
        
        response = self._make_mcp_tool_request("search_shop_catalog", arguments)
        response_products = json.loads(response["content"][0]["text"])["products"]
        
        # Find the product with matching ID
        for product_data in response_products:
            if product_data.get("product_id") == product_id or any(v.get("variant_id") == product_id for v in product_data.get("variants", [])):
                # Process similar to search_products
                variants = []
                for variant_data in product_data.get("variants", []):
                    # Handle price from variant's price_range if available
                    if "price_range" in variant_data:
                        variant_price = float(variant_data["price_range"].get("min", "0.00"))
                        variant_currency = variant_data["price_range"].get("currency", "USD")
                    else:
                        variant_price = float(variant_data.get("price", "0.00"))
                        variant_currency = variant_data.get("currency", "USD")
                    
                    variant = {
                        "id": variant_data["variant_id"],
                        "title": variant_data["title"],
                        "available": variant_data.get("available", True),  # Default to True if not present
                        "price": variant_price,
                        "currency": variant_currency,
                        "image_url": variant_data.get("image_url", "")
                    }
                    variants.append(variant)
                
                images = product_data.get("images", [])
                
                # Extract price from price_range
                price_range = product_data.get("price_range", {})
                price = float(price_range.get("min", "0.00"))
                currency = price_range.get("currency", "USD")
                
                return Product(
                    id=product_data["product_id"],
                    title=product_data["title"],
                    description=product_data.get("description", ""),
                    handle=product_data.get("handle", ""),
                    price=price,
                    currency=currency,
                    variants=variants,
                    images=images
                )
        
        return None
    
    def create_cart(self) -> str:
        """Create a new cart using Shopify MCP update_cart tool."""
        # Create new cart by calling update_cart without cart_id
        response = self._make_mcp_tool_request("update_cart", {
            "add_items": []  # Empty add_items array creates new cart
        })
        
        print("=== CREATE CART RESPONSE ===")
        print(response)
        print("=============================")
        
        # Parse the MCP response structure
        if "content" in response and len(response["content"]) > 0:
            # Parse JSON content from MCP response
            content = json.loads(response["content"][0]["text"])
            if "cart" in content and "id" in content["cart"]:
                return content["cart"]["id"]
        
        # Fallback to other possible structures
        if "cart_id" in response:
            return response["cart_id"]
        elif "cart" in response:
            return response["cart"].get("id")
        else:
            # Return None if no cart_id found
            return None
    
    def add_to_cart(self, cart_id: str, variant_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Add item to cart using Shopify MCP update_cart tool."""
        arguments = {
            "cart_id": cart_id,
            "add_items": [{
                "product_variant_id": variant_id,
                "quantity": quantity
            }]
        }
        
        print("=== ADD TO CART REQUEST ===")
        print(f"Cart ID: {cart_id}")
        print(f"Variant ID: {variant_id}")
        print(f"Quantity: {quantity}")
        print(f"Arguments: {arguments}")
        print("===========================")
        
        response = self._make_mcp_tool_request("update_cart", arguments)
        
        print("=== ADD TO CART RESPONSE ===")
        print(response)
        print("============================")
        
        # Parse the MCP response structure
        if "content" in response and len(response["content"]) > 0:
            content = json.loads(response["content"][0]["text"])
            return content
        
        return response
    
    def remove_from_cart(self, cart_id: str, line_item_id: str) -> Dict[str, Any]:
        """Remove item from cart using Shopify MCP update_cart tool."""
        arguments = {
            "cart_id": cart_id,
            "update_items": [{
                "id": line_item_id,
                "quantity": 0  # Set quantity to 0 to remove item
            }]
        }
        response = self._make_mcp_tool_request("update_cart", arguments)
        
        # Parse the MCP response structure
        if "content" in response and len(response["content"]) > 0:
            content = json.loads(response["content"][0]["text"])
            return content
        
        return response
    
    def get_cart(self, cart_id: str) -> Dict[str, Any]:
        """Get cart contents using Shopify MCP get_cart tool."""
        arguments = {"cart_id": cart_id}
        response = self._make_mcp_tool_request("get_cart", arguments)
        
        # Parse the MCP response structure
        if "content" in response and len(response["content"]) > 0:
            content = json.loads(response["content"][0]["text"])
            return content
        
        return response
    

