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

def update_user_item_status(uuid: str, item_id: str, status: str) -> Dict:
    resp = supabase.table("user_item").update({"status": status}).eq("uuid", uuid).eq("item_id", item_id).execute()
    return resp.data 