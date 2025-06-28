#!/usr/bin/env python3
"""
Simple server startup script for the Profiling Agent MCP Server.
This script properly handles imports and starts the FastAPI server.
"""

import os
import sys
import uvicorn
from pathlib import Path

# --- Add project root to sys.path ---
# This ensures that imports like `from backend.db...` work correctly.
# The project root is three levels up from this script's directory.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Now that the path is set, we can import the FastAPI app using an absolute path
from backend.profiling_agent.src.main import app

# Load environment variables from the root .env file
from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / ".env")

if __name__ == "__main__":
    # Use a specific environment variable for this agent's port
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PROFILING_AGENT_PORT", "8080"))
    
    print(f"🚀 Starting Profiling Agent MCP Server on http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    # We pass the app as a string to uvicorn for robust reloading.
    # This is more stable than passing the app object directly.
    uvicorn.run(
        "backend.profiling_agent.src.main:app",
        host=host,
        port=port,
        reload=True,
        # Specify the directory to watch for changes
        reload_dirs=[str(project_root / "backend/profiling_agent/src")]
    ) 