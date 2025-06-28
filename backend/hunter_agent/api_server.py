import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
import os

if __name__ == "__main__":
    # Optionally load environment variables from root .env
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=project_root / ".env")
    except Exception:
        pass

    port = int(os.getenv("HUNTER_AGENT_PORT", "8090"))
    print(f"🚀 Starting Hunter Agent API on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    uvicorn.run(
        "backend.hunter_agent.api:app",
        host="0.0.0.0",
        port=port,
        reload=True
    ) 