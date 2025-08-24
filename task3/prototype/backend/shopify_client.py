"""Shopify Storefront MCP client for product search.
Based on task2 implementation but simplified for fetching products.
"""
import json
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from config import config

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

class ShopifyStorefrontClient:
    """Simplified Shopify client for fetching products."""
    
    def __init__(self):
        self.store_url = config.SHOPIFY_STORE_URL
        self.mcp_endpoint = f"https://{self.store_url}/api/mcp"
        self.headers = {"Content-Type": "application/json"}
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
        tool_name = "search_shop_catalog"
        arguments = {
            "query": query,
            "context": f"Customer searching for {query}"
        }
        
        response = self._make_mcp_tool_request(tool_name, arguments)
        response_products = json.loads(response["content"][0]["text"])["products"]
        
        products = []
        for product_data in response_products:
            # Extract variants
            variants = []
            for variant_data in product_data.get("variants", []):
                if "price_range" in variant_data:
                    variant_price = float(variant_data["price_range"].get("min", "0.00"))
                    variant_currency = variant_data["price_range"].get("currency", "USD")
                else:
                    variant_price = float(variant_data.get("price", "0.00"))
                    variant_currency = variant_data.get("currency", "USD")
                
                variant = {
                    "id": variant_data["variant_id"],
                    "title": variant_data["title"],
                    "available": variant_data.get("available", True),
                    "price": variant_price,
                    "currency": variant_currency,
                    "image_url": variant_data.get("image_url", "")
                }
                variants.append(variant)
            
            # Extract main image
            image_url = product_data.get("image_url", "")
            
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
    
    def get_all_products(self, target_count: int = 500) -> List[Product]:
        """Fetch as many products as possible by searching with various terms."""
        all_products = []
        product_ids = set()
        
        # Search terms to get diverse products
        search_terms = [
            "shirt", "dress", "shoes", "bag", "hat", "jacket", "pants", "sweater",
            "jewelry", "watch", "sunglasses", "scarf", "belt", "coat", "skirt",
            "jeans", "boots", "sneakers", "sandals", "earrings", "necklace",
            "blue", "red", "black", "white", "green", "yellow", "pink", "brown",
            "cotton", "leather", "silk", "wool", "denim", "canvas", "metal",
            "summer", "winter", "casual", "formal", "sport", "work", "party",
            "men", "women", "kids", "unisex", "small", "medium", "large",
            "cheap", "expensive", "sale", "new", "popular", "trending"
        ]
        
        for term in search_terms:
            if len(all_products) >= target_count:
                break
                
            try:
                print(f"Searching for: {term}")
                products = self.search_products(term, limit=20)
                
                for product in products:
                    if product.id not in product_ids and len(all_products) < target_count:
                        all_products.append(product)
                        product_ids.add(product.id)
                        
            except Exception as e:
                print(f"Error searching for '{term}': {e}")
                continue
        
        print(f"Fetched {len(all_products)} unique products")
        return all_products
