#!/usr/bin/env python3
"""
Hunter Agent Main Entry Point

Runs the consolidated Hunter Agent API server that provides:
- Complete Supabase-based workflow for user data storage
- Candidate generation with embedding-based retrieval
- Personalized recommendations after user swipes
- 3-month plan generation with plan_agent integration

This replaces the separate api.py, integrated_api.py, and supabase_api.py files.
"""

import uvicorn
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Import the consolidated API
from api import app

def main():
    """Run the Hunter Agent API server."""
    print("🚀 Starting Hunter Agent Consolidated API Server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True  # Enable auto-reload for development
    )

if __name__ == "__main__":
    main()