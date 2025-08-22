"""
Run script for the Intercom RAG Backend.
"""
import uvicorn
from config import config

def main():
    """Run the FastAPI application."""
    print("Starting Intercom RAG Backend...")
    print(f"Backend will be available at: http://localhost:8000")
    print(f"API docs will be available at: http://localhost:8000/docs")
    
    if config.OPENAI_API_KEY == "your_openai_api_key_here":
        print("\n⚠️  WARNING: OpenAI API key not set!")
        print("Please set your OpenAI API key in the .env file or as an environment variable.")
        print("OPENAI_API_KEY=your_actual_api_key")
        
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
