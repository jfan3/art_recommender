from dotenv import load_dotenv
import os
from supabase import create_client, Client
from typing import List, Dict, Any, Optional

# Load environment variables from .env in the root folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Service Role Key must be set as environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- USER PROFILE ---
def upsert_user_profile(profile: Dict[str, Any]) -> Dict:
    resp = supabase.table("user_profile").upsert(profile).execute()
    return resp.data

def get_user_profile(uuid: str) -> Optional[Dict]:
    resp = supabase.table("user_profile").select("*").eq("uuid", uuid).single().execute()
    return resp.data if resp.data else None

def set_user_profile_complete(uuid: str) -> Dict:
    resp = supabase.table("user_profile").update({"complete": True}).eq("uuid", uuid).execute()
    return resp.data

# --- ITEM ---
def upsert_item(item: Dict[str, Any]) -> Dict:
    resp = supabase.table("item").upsert(item).execute()
    return resp.data

def get_item(item_id: str) -> Optional[Dict]:
    resp = supabase.table("item").select("*").eq("item_id", item_id).single().execute()
    return resp.data if resp.data else None

# --- USER ITEM ---
def upsert_user_item(user_item: Dict[str, Any]) -> Dict:
    resp = supabase.table("user_item").upsert(user_item).execute()
    return resp.data

def get_user_items(uuid: str) -> List[Dict]:
    resp = supabase.table("user_item").select("*").eq("uuid", uuid).execute()
    return resp.data if resp.data else []

def update_user_item_status(uuid: str, item_id: str, status: str) -> bool:
    try:
        # First try to update existing record
        resp = supabase.table("user_item").update({"status": status}).eq("uuid", uuid).eq("item_id", item_id).execute()
        
        # If no rows were updated, insert new record
        if not resp.data:
            user_item_data = {
                "uuid": uuid,
                "item_id": item_id,
                "status": status
            }
            resp = supabase.table("user_item").insert(user_item_data).execute()
        
        return True  # Return True if successful
    except Exception as e:
        print(f"❌ Error updating user_item status: {e}")
        return False

# --- USER PLAN ---
def upsert_user_plan(plan_data: Dict[str, Any]) -> Dict:
    """Store or update a user's weekly plan in Supabase."""
    resp = supabase.table("user_plan").upsert(plan_data).execute()
    return resp.data

def get_user_plan(uuid: str) -> Optional[Dict]:
    """Retrieve a user's plan from Supabase."""
    resp = supabase.table("user_plan").select("*").eq("uuid", uuid).single().execute()
    return resp.data if resp.data else None

def delete_user_plan(uuid: str) -> Dict:
    """Delete a user's plan from Supabase."""
    resp = supabase.table("user_plan").delete().eq("uuid", uuid).execute()
    return resp.data

# --- USER EMBEDDINGS ---
def upsert_user_embedding(uuid: str, embedding: List[float], version: int = 1) -> Dict:
    """Store or update user embedding in database."""
    embedding_data = {
        "uuid": uuid,
        "embedding": embedding,
        "version": version,
        "updated_at": "now()"
    }
    resp = supabase.table("user_embedding").upsert(embedding_data).execute()
    return resp.data

def get_user_embedding(uuid: str) -> Optional[Dict]:
    """Retrieve the latest user embedding."""
    resp = supabase.table("user_embedding").select("*").eq("uuid", uuid).order("version", desc=True).limit(1).execute()
    return resp.data[0] if resp.data else None

# --- ITEM EMBEDDINGS ---
def upsert_item_embedding(item_id: str, embedding: List[float]) -> Dict:
    """Store or update item embedding in database."""
    embedding_data = {
        "item_id": item_id,
        "embedding": embedding,
        "updated_at": "now()"
    }
    resp = supabase.table("item_embedding").upsert(embedding_data).execute()
    return resp.data

def get_item_embedding(item_id: str) -> Optional[Dict]:
    """Retrieve item embedding."""
    resp = supabase.table("item_embedding").select("*").eq("item_id", item_id).single().execute()
    return resp.data if resp.data else None

def get_items_with_embeddings(item_ids: List[str]) -> List[Dict]:
    """Retrieve items with their embeddings."""
    if not item_ids:
        return []
    
    # Get items
    items_resp = supabase.table("item").select("*").in_("item_id", item_ids).execute()
    items = {item["item_id"]: item for item in items_resp.data} if items_resp.data else {}
    
    # Get embeddings
    embeddings_resp = supabase.table("item_embedding").select("*").in_("item_id", item_ids).execute()
    embeddings = {emb["item_id"]: emb["embedding"] for emb in embeddings_resp.data} if embeddings_resp.data else {}
    
    # Combine items with embeddings
    results = []
    for item_id in item_ids:
        if item_id in items and item_id in embeddings:
            item = items[item_id].copy()
            item["embedding"] = embeddings[item_id]
            results.append(item)
    
    return results 