"""
Run script for the Intercom RAG Frontend.
"""
import subprocess
import sys
import os

def main():
    """Run the Streamlit application."""
    print("Starting Intercom RAG Frontend...")
    print("Frontend will be available at: http://localhost:8501")
    print("Make sure the backend is running at: http://localhost:8000")
    print("\nStarting Streamlit...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down frontend...")
        sys.exit(0)

if __name__ == "__main__":
    main()

