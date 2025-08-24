#!/usr/bin/env python3
"""
Complete data pipeline runner for the recommendation system prototype.
This script orchestrates the entire process from data fetching to recommendation generation.
"""
import os
import sys
import time
import subprocess
from dotenv import load_dotenv

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"COMMAND: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("STDOUT:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print("STDERR:", e.stderr)
        print("STDOUT:", e.stdout)
        return False

def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check if we're in the right directory
    if not os.path.exists("backend/config.py"):
        print("❌ Error: Please run this script from the prototype directory")
        return False
    
    # Load environment variables from backend/.env
    backend_env_path = "backend/.env"
    if os.path.exists(backend_env_path):
        from dotenv import load_dotenv
        load_dotenv(backend_env_path)
        print("✅ Loaded environment variables from backend/.env")
    
    # Check for environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("💡 Tip: Create backend/.env file with your API key")
        return False
    
    # Check if Qdrant is running (simple check)
    try:
        import requests
        response = requests.get("http://localhost:6333/collections", timeout=5)
        print("✅ Qdrant is running")
    except:
        print("❌ Error: Qdrant is not running on localhost:6333")
        print("💡 Tip: Run 'docker run -p 6333:6333 qdrant/qdrant:latest'")
        return False
    
    return True

def main():
    """Run the complete data pipeline."""
    print("🚀 Starting Product Recommendation System Data Pipeline")
    print("📋 This will:")
    print("   1. Fetch products from Shopify")
    print("   2. Generate embeddings and store in Qdrant") 
    print("   3. Create mock interaction data")
    print("   4. Calculate co-occurrence and lift scores")
    print("   5. Generate recommendations for all products")
    
    if not check_prerequisites():
        sys.exit(1)
    
    # Change to backend directory
    os.chdir("backend")
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Step 1: Fetch products and generate embeddings
    if not run_command("python data_fetcher.py", "Fetching products and generating embeddings"):
        print("❌ Pipeline failed at data fetching step")
        sys.exit(1)
    
    # Step 2: Generate recommendations
    if not run_command("python recommendation_engine.py", "Generating recommendations"):
        print("❌ Pipeline failed at recommendation generation step")
        sys.exit(1)
    
    # Summary
    print(f"\n{'='*60}")
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    print("📊 Data files created:")
    print("   - data/products.json")
    print("   - data/interactions.json") 
    print("   - data/co_occurrence.json")
    print("   - data/lift_scores.json")
    print("   - data/recommendations.json")
    print("\n🚀 Next steps:")
    print("   1. Start the API server: python main.py")
    print("   2. Start the frontend: streamlit run ../frontend/app.py")
    print("   3. Or use Docker: docker-compose up")
    
if __name__ == "__main__":
    main()
