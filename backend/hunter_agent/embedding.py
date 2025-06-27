# tools/embedding.py
import json
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Make sure your OpenAI API key is set in the environment
openai.api_key = os.getenv("OPENAI_API_KEY")

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

def generate_user_embedding(json_path):
    profile_text = extract_profile_text(json_path)
    
    response = openai.embeddings.create(
        input=profile_text,
        model="text-embedding-ada-002"
    )
    
    embedding = response.data[0].embedding
    return embedding 