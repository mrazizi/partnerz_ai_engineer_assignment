"""Configuration settings for the Shopify Conversational Agent."""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Shopify Configuration
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "amirtest100.myshopify.com")

# LLM Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

# Conversation Configuration
MAX_CONVERSATION_HISTORY = os.getenv("MAX_CONVERSATION_HISTORY", 20)
SEARCH_RESULTS_LIMIT = os.getenv("SEARCH_RESULTS_LIMIT", 10)
