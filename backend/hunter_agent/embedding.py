# tools/embedding.py
import json
import openai
import os
from dotenv import load_dotenv
from retriever import load_user_profile
from db.supabase_client import upsert_user_embedding, get_user_embedding
import numpy as np

# Load environment variables from .env in the root folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Make sure your OpenAI API key is set in the environment
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_type = "openai"

def extract_profile_text(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    # The 'data' object is the user profile itself.
    profile_text = ""
    
    # Handle past_favorite_work as a list
    past_favorites = data.get('past_favorite_work', [])
    if isinstance(past_favorites, list):
        profile_text += f"Past favorites: {', '.join(past_favorites)}. "
    else:
        profile_text += f"Past favorites: {past_favorites}. "
    
    # Use the correct field name for genre preference
    profile_text += f"Genre: {data.get('taste_genre', '')}. "
    
    # Handle current_obsession as a list
    current_obsession = data.get('current_obsession', [])
    if isinstance(current_obsession, list):
        profile_text += f"Current obsession: {', '.join(current_obsession)}. "
    else:
        profile_text += f"Current obsession: {current_obsession}. "
    
    # Use the correct field name for state of mind
    profile_text += f"Current state of mind: {data.get('state_of_mind', '')}. "
    
    # Use the correct field name for future aspirations
    profile_text += f"Future aspirations: {data.get('future_aspirations', '')}. "
    
    # Add profile completion status if available
    if 'complete' in data:
        completion_status = "complete" if data.get('complete', False) else "incomplete"
        profile_text += f"Profile status: {completion_status}. "
    
    return profile_text.strip()

def extract_profile_text_from_dict(profile: dict) -> str:
    # Concatenate relevant fields for embedding
    fields = [
        'past_favorite_work', 'taste_genre', 'current_obsession',
        'state_of_mind', 'future_aspirations'
    ]
    text_parts = []
    for field in fields:
        value = profile.get(field, "")
        if isinstance(value, list):
            text_parts.append(", ".join(value))
        else:
            text_parts.append(str(value))
    return "; ".join(text_parts)

def generate_user_embedding(user_uuid_or_profile, store_in_db: bool = True):
    """Generate user embedding and optionally store in database."""
    if isinstance(user_uuid_or_profile, dict):
        profile = user_uuid_or_profile
        user_uuid = profile.get("uuid")
    else:
        user_uuid = user_uuid_or_profile
        profile = load_user_profile(user_uuid)
    
    # Check if embedding already exists
    if store_in_db and user_uuid:
        existing_embedding = get_user_embedding(user_uuid)
        if existing_embedding:
            print(f"Using existing user embedding for {user_uuid}")
            return existing_embedding["embedding"]
    
    profile_text = extract_profile_text_from_dict(profile)
    
    response = openai.embeddings.create(
        input=profile_text,
        model="text-embedding-ada-002"
    )
    
    embedding = response.data[0].embedding
    
    # Store in database if requested
    if store_in_db and user_uuid:
        upsert_user_embedding(user_uuid, embedding, version=1)
        print(f"Stored new user embedding for {user_uuid}")
    
    return embedding

# For demonstration, return a dummy embedding (replace with real model call)
def generate_user_embedding_dummy(user_uuid_or_profile):
    if isinstance(user_uuid_or_profile, dict):
        profile = user_uuid_or_profile
    else:
        profile = load_user_profile(user_uuid_or_profile)
    profile_text = extract_profile_text_from_dict(profile)
    return np.random.rand(128).tolist() 