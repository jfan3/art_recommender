# tools/embedding.py
import json
import openai
import os

# Make sure your OpenAI API key is set in the environment
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_profile_text(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    # The 'data' object is the user profile itself.
    profile_text = ""
    # The 'past_favorite_work' is a string, not a list.
    profile_text += f"Past favorites: {data.get('past_favorite_work', '')}. "
    # Correcting the key for genre preference.
    profile_text += f"Genre: {data.get('descriptions_of_users_taste_genre_preference', '')}. "
    # 'current_obsession' is not in the sample JSON, so we'll skip it for now.
    # Correcting the key for state of mind.
    profile_text += f"Current state of mind: {data.get('users_current_state_of_mind', '')}. "
    # Correcting the key for future aspirations.
    profile_text += f"Future aspirations: {data.get('users_future_aspirations', '')}. "
    return profile_text.strip()

def generate_user_embedding(json_path):
    profile_text = extract_profile_text(json_path)
    
    response = openai.embeddings.create(
        input=profile_text,
        model="text-embedding-ada-002"
    )
    
    embedding = response.data[0].embedding
    return embedding 