from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from backend.db.supabase_client import get_user_items, get_item, update_user_item_status, upsert_item, upsert_user_item, set_user_profile_complete
from backend.hunter_agent.retriever import load_user_profile, retrieve_top_candidates
from backend.hunter_agent.embedding import generate_user_embedding
from backend.hunter_agent.art_embedding import batch_generate_embeddings
import numpy as np
import traceback
import hashlib

# In-memory status store (for demo; replace with persistent store for production)
generation_status = {}

def generate_item_id(url: str) -> str:
    """Generate a consistent item_id from a URL using SHA-256."""
    # Use SHA-256 to generate a hash of the URL
    hash_object = hashlib.sha256(url.encode())
    # Take first 12 characters of the hex digest for a shorter but still unique ID
    return hash_object.hexdigest()[:12]

def count_right_swipes(user_uuid: str) -> int:
    """Count how many right swipes a user has made."""
    user_items = get_user_items(user_uuid)
    return sum(1 for item in user_items if item["status"] == "swipe_right")

app = FastAPI(title="Hunter Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SwipeRequest(BaseModel):
    user_uuid: str
    item_id: str
    status: str  # 'swipe_left', 'swipe_right', 'shortlisted', 'confirmed', etc.

@app.get("/api/candidates/{user_uuid}")
def get_candidates(user_uuid: str):
    # First check if user has reached 30 right swipes
    right_swipes = count_right_swipes(user_uuid)
    if right_swipes >= 30:
        return {"candidates": [], "training_complete": True}

    user_items = get_user_items(user_uuid)
    candidate_ids = [ui["item_id"] for ui in user_items if ui["status"] == "candidate"]
    candidates = []
    for item_id in candidate_ids:
        item = get_item(item_id)
        if item:
            candidates.append(item)
    return {"candidates": candidates, "training_complete": False}

@app.post("/api/swipe")
def swipe(req: SwipeRequest):
    # Convert URL to item_id if a URL was passed
    item_id = req.item_id
    if item_id.startswith('http'):
        item_id = generate_item_id(item_id)
    
    # Update the user_item status
    result = update_user_item_status(req.user_uuid, item_id, req.status)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update swipe status.")
    
    # Check if we've reached 30 right swipes
    if req.status == "swipe_right":
        right_swipes = count_right_swipes(req.user_uuid)
        if right_swipes >= 30:
            return {"success": True, "training_complete": True}
    
    return {"success": True, "training_complete": False}

@app.get("/api/generation_status/{user_uuid}")
def get_generation_status(user_uuid: str):
    status = generation_status.get(user_uuid, "pending")
    return {"status": status}

@app.post("/api/generate_candidates/{user_uuid}")
def generate_candidates(user_uuid: str, request: Request):
    print(f"[INFO] Hunter Agent received candidate generation trigger for UUID: {user_uuid}")
    print(f"[DEBUG] Request method: {request.method}, headers: {dict(request.headers)}")
    print(f"[DEBUG] Call stack:\n{''.join(traceback.format_stack())}")
    generation_status[user_uuid] = "pending"
    # Load user profile from Supabase
    user_profile = load_user_profile(user_uuid)
    if not user_profile or user_profile.get("uuid") != user_uuid:
        print(f"[WARN] No user profile found for UUID: {user_uuid}")
        generation_status[user_uuid] = "pending"
        return {"error": "User profile not found or does not match."}
    user_embedding = generate_user_embedding(user_uuid)
    # Retrieve candidates from all domains
    movie_candidates = retrieve_top_candidates("movies", user_embedding, user_profile)
    book_candidates = retrieve_top_candidates("books", user_embedding, user_profile)
    music_candidates = retrieve_top_candidates("music", user_embedding, user_profile)
    art_candidates = retrieve_top_candidates("art", user_embedding, user_profile)
    poetry_candidates = retrieve_top_candidates("poetry", user_embedding, user_profile)
    podcast_candidates = retrieve_top_candidates("podcasts", user_embedding, user_profile)
    musical_candidates = retrieve_top_candidates("musicals", user_embedding, user_profile)
    # Merge and enrich
    top_candidates = movie_candidates + book_candidates + music_candidates + art_candidates + poetry_candidates + podcast_candidates + musical_candidates
    top_candidates = batch_generate_embeddings(top_candidates)
    # Log to Supabase
    for candidate in top_candidates:
        item_id = generate_item_id(candidate.get("source_url", ""))
        item_data = {
            "item_id": item_id,
            "item_name": candidate.get("title", ""),
            "description": candidate.get("description", ""),
            "source_url": candidate.get("source_url", ""),
            "image_url": candidate.get("image_url", ""),
            "category": candidate.get("category", ""),
            "creator": candidate.get("creator", ""),
            "release_date": candidate.get("release_date", ""),
            "metadata": candidate.get("metadata", {})
        }
        upsert_item(item_data)
        user_item_data = {
            "uuid": user_uuid,
            "item_id": item_id,
            "status": "candidate"
        }
        upsert_user_item(user_item_data)
    generation_status[user_uuid] = "complete"
    set_user_profile_complete(user_uuid)
    print(f"[INFO] Hunter Agent finished candidate generation for UUID: {user_uuid} ({len(top_candidates)} candidates)")
    return {"success": True, "candidates_generated": len(top_candidates)} 