#!/usr/bin/env python3
"""
Simple server startup script for the Profiling Agent MCP Server.
This script properly handles imports and starts the FastAPI server.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    print(f"🚀 Starting Profiling Agent MCP Server on http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    # Use import string for proper reload functionality
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=True,
        reload_dirs=[str(src_path)]
    ) 