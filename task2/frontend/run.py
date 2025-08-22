"""Run script for the frontend Streamlit app."""
import streamlit.web.cli as stcli
import sys

if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false"
    ]
    sys.exit(stcli.main())
