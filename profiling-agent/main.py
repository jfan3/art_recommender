import uuid
from fastapi import FastAPI
from pydantic import BaseModel, Field
import json
import os
from typing import List, Dict, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
DATA_STORE_FILE = "user_profiles.json"

# --- Azure OpenAI Client ---
try:
    client = AzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
    )
    MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
except TypeError:
    client = None
    MODEL_NAME = None
    print("Azure OpenAI credentials not found. The agent will not work. Please create a .env file.")


# --- Data Models ---

class UserProfile(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    past_favorite_work: List[str] = Field(default=[], description="A list of the user's all-time favorite works of art (movies, books, music, etc.).")
    favorite_taste_genre_description: str = Field(default="", description="A summary of the user's overall taste and preferred genres.")
    current_obsession: List[str] = Field(default=[], description="What the user is currently obsessed with or can't stop thinking about.")
    current_state_of_mind: str = Field(default="", description="The user's current emotional or mental state (e.g., adventurous, introspective, stressed).")
    future_aspirations: str = Field(default="", description="The user's future goals or who they aspire to be like in the future.")

class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: str
    message: str
    conversation_history: List[Dict[str, str]]

class ChatResponse(BaseModel):
    agent_response: str
    session_id: str
    user_id: str
    profiling_complete: bool = False

# --- Data Storage ---

def load_user_profiles() -> Dict[str, UserProfile]:
    if not os.path.exists(DATA_STORE_FILE):
        return {}
    try:
        with open(DATA_STORE_FILE, "r") as f:
            data = json.load(f)
            return {uid: UserProfile(**profile_data) for uid, profile_data in data.items()}
    except (json.JSONDecodeError, IOError):
        return {}


def save_user_profile(profile: UserProfile):
    profiles = load_user_profiles()
    profiles[profile.uuid] = profile
    with open(DATA_STORE_FILE, "w") as f:
        json.dump({uid: p.dict() for uid, p in profiles.items()}, f, indent=4)

# In-memory session store for active conversations
session_state: Dict[str, UserProfile] = {}


# --- System Prompt for the Agent ---
SYSTEM_PROMPT = """
You are a friendly and insightful Profiler Agent. Your goal is to understand a user's personality and tastes by asking them a series of questions.
You need to fill out a user profile with the following fields:
- past_favorite_work: A list of their favorite art.
- favorite_taste_genre_description: A summary of their tastes.
- current_obsession: What they are currently fascinated by.
- current_state_of_mind: Their current mood or mindset.
- future_aspirations: Their future goals or who they admire.

Your task is to:
1.  Initiate the conversation.
2.  Ask questions one by one to gather information for each field.
3.  Keep your questions conversational and engaging.
4.  Analyze the user's responses and update the user profile JSON object.
5.  Reflect on the current state of the profile. If all fields are reasonably filled, set 'profiling_complete' to true.
6.  Your final response MUST be a single JSON object containing two keys: 'agent_response' (your next question or concluding statement) and 'updated_profile' (the user's profile with your updates).

Example Conversation Flow:
- You: "Hello! To get started, what are some of your all-time favorite works of art?"
- User: "I love the movie Inception and the book 'Project Hail Mary'."
- You: (Updates profile) "That's a great mix of sci-fi! How would you describe your overall taste?"
...and so on, until all fields are filled.
"""

# --- FastAPI App ---

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """Load existing user profiles into memory on startup."""
    if not os.path.exists(DATA_STORE_FILE):
        with open(DATA_STORE_FILE, "w") as f:
            json.dump({}, f)
    profiles = load_user_profiles()
    global session_state
    session_state = profiles.copy()


@app.post("/v1/profiler/chat", response_model=ChatResponse)
async def chat_with_profiler(request: ChatRequest):
    """
    Handles the chat interaction for profiling a user using an LLM.
    """
    if not client:
        return ChatResponse(
            agent_response="Error: Azure OpenAI client is not configured. Please check your .env file.",
            session_id=request.session_id,
            user_id=request.user_id or "unknown",
            profiling_complete=True,
        )

    # --- 1. Get or Create User Profile ---
    if request.user_id and request.user_id in session_state:
        user_profile = session_state[request.user_id]
    elif request.user_id:
        profiles = load_user_profiles()
        user_profile = profiles.get(request.user_id, UserProfile())
        session_state[user_profile.uuid] = user_profile
    else:
        user_profile = UserProfile()
        session_state[user_profile.uuid] = user_profile

    # --- 2. Construct messages for the LLM ---
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history
    messages.extend(request.conversation_history)
    
    # Add the current state of the user profile and the user's latest message
    messages.append({
        "role": "user",
        "content": f"Here is the current user profile to be updated:\n{user_profile.json(indent=2)}\n\nAnd here is the latest message from the user:\n'{request.message}'"
    })

    # --- 3. Call Azure OpenAI ---
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        response_content = completion.choices[0].message.content
        response_data = json.loads(response_content)
        
        agent_response = response_data.get("agent_response", "I'm sorry, I seem to be having trouble thinking right now.")
        updated_profile_data = response_data.get("updated_profile", {})

        # --- 4. Update and Save Profile ---
        new_profile = UserProfile(**updated_profile_data)
        session_state[user_profile.uuid] = new_profile
        save_user_profile(new_profile)

        # --- 5. Check for completion ---
        # A simple check: if all fields have some value. The LLM might not set this perfectly.
        profiling_complete = all([
            new_profile.past_favorite_work,
            new_profile.favorite_taste_genre_description,
            new_profile.current_obsession,
            new_profile.current_state_of_mind,
            new_profile.future_aspirations
        ])

    except Exception as e:
        print(f"Error calling OpenAI or processing response: {e}")
        agent_response = "I'm having trouble connecting right now. Let's try again in a moment."
        profiling_complete = False

    return ChatResponse(
        agent_response=agent_response,
        session_id=request.session_id,
        user_id=user_profile.uuid,
        profiling_complete=profiling_complete,
    )

if __name__ == "__main__":
    import uvicorn
    if not client:
        print("Cannot start server: Azure OpenAI client is not configured.")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000) 