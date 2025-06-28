import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json

# Handle imports for both direct execution and package import
try:
    from .chat_loop import ChatLoop
except ImportError:
    from chat_loop import ChatLoop

# Load environment variables from .env in the root folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

app = FastAPI(title="Profiling Agent MCP Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chat loop
chat_loop = ChatLoop()

class ChatRequest(BaseModel):
    session_id: str
    messages: List[Dict[str, str]]
    user_uuid: str = None

class ProfileResponse(BaseModel):
    uuid: str
    past_favorite_work: List[str]
    taste_genre: str
    current_obsession: List[str]
    state_of_mind: str
    future_aspirations: str
    complete: bool
    created_at: str
    updated_at: str

class ConversationResponse(BaseModel):
    session_id: str
    user_uuid: str
    messages: List[Dict[str, str]]
    created_at: str
    updated_at: str

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Profiling Agent MCP Server is running"}

@app.get("/schema")
async def get_schema():
    """Return the MCP tool schema."""
    return chat_loop.get_tool_schema()

@app.post("/chat")
async def chat(request: ChatRequest):
    """Stream chat response with tool calls and conversation persistence."""
    
    def generate():
        try:
            for chunk in chat_loop.chat_stream(
                session_id=request.session_id,
                messages=request.messages,
                user_uuid=request.user_uuid
            ):
                yield chunk
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/profiles/{user_uuid}")
async def get_profile(user_uuid: str):
    """Get a user profile by UUID."""
    profile = chat_loop.get_profile(user_uuid)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.get("/profiles")
async def list_profiles():
    """List all profile UUIDs."""
    return {"profiles": chat_loop.list_profiles()}

@app.post("/profiles")
async def create_profile():
    """Create a new profile and return the UUID."""
    print("[DEBUG] /profiles POST called: creating new profile")
    user_uuid = chat_loop.storage.create_profile()
    print(f"[DEBUG] New profile created with UUID: {user_uuid}")
    return {"uuid": user_uuid}

@app.get("/conversations")
async def list_conversations():
    """List all conversation session IDs."""
    return {"conversations": chat_loop.list_conversations()}

@app.get("/conversations/{session_id}")
async def get_conversation(session_id: str):
    """Get a conversation by session ID."""
    conversation = chat_loop.get_conversation(session_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.get("/conversations/user/{user_uuid}")
async def get_conversations_by_user(user_uuid: str):
    """Get all conversations for a specific user."""
    conversations = chat_loop.get_conversations_by_user(user_uuid)
    return {"conversations": conversations}

@app.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str):
    """Delete a conversation by session ID."""
    success = chat_loop.delete_conversation(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}

@app.get("/conversations/{session_id}/messages")
async def get_conversation_messages(session_id: str):
    """Get just the messages from a conversation."""
    messages = chat_loop.storage.get_messages(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"messages": messages}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host=host, port=port) 