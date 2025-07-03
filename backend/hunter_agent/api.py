from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from backend.db.supabase_client import get_user_items, get_item, update_user_item_status, upsert_item, upsert_user_item, set_user_profile_complete
from backend.hunter_agent.retriever import load_user_profile, retrieve_top_candidates
from backend.hunter_agent.embedding import generate_user_embedding
from backend.hunter_agent.art_embedding import batch_generate_embeddings
from backend.hunter_agent.reranker import update_user_embedding_from_swipes, get_personalized_candidates
import numpy as np
import traceback
import hashlib
import json
import os
import sys
from pathlib import Path

# Add plan_agent to Python path
plan_agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plan_agent')
if plan_agent_path not in sys.path:
    sys.path.append(plan_agent_path)

# Import plan_agent functions
try:
    from main import generate_smart_weekly_plan, get_media_time_estimate
except ImportError as e:
    print(f"Warning: Could not import plan_agent functions: {e}")
    generate_smart_weekly_plan = None
    get_media_time_estimate = None

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

def generate_three_month_plan(user_uuid: str, personalized_candidates: list) -> dict:
    """Generate a 3-month plan using plan_agent with personalized candidates."""
    try:
        if not generate_smart_weekly_plan:
            return {"success": False, "error": "Plan agent not available"}
        
        if not personalized_candidates:
            return {"success": False, "error": "No personalized candidates available"}
        
        # Format candidates for plan_agent (ensure they have required fields)
        formatted_candidates = []
        for candidate in personalized_candidates:
            formatted_candidate = {
                "title": candidate.get("item_name", candidate.get("title", "Unknown")),
                "type": candidate.get("category", "art").lower(),
                "description": candidate.get("description", ""),
                "source_url": candidate.get("source_url", ""),
                "image_url": candidate.get("image_url", ""), 
                "score": candidate.get("score", 0.5),
                "category": candidate.get("category", "art"),
                "creator": candidate.get("creator", ""),
                "metadata": candidate.get("metadata", {})
            }
            formatted_candidates.append(formatted_candidate)
        
        # Generate 3-month plan (12 weeks) with medium effort level
        print(f"Generating 3-month plan for user {user_uuid} with {len(formatted_candidates)} candidates")
        weekly_plan = generate_smart_weekly_plan(formatted_candidates, num_weeks=12, effort_level="medium")
        
        # Save plan to user-specific file
        plan_filename = f"user_plan_{user_uuid}.json"
        plan_filepath = os.path.join(os.path.dirname(__file__), "..", "plan_agent", plan_filename)
        
        try:
            os.makedirs(os.path.dirname(plan_filepath), exist_ok=True)
            with open(plan_filepath, 'w', encoding='utf-8') as f:
                json.dump(weekly_plan, f, indent=2, ensure_ascii=False)
            print(f"Saved plan to {plan_filepath}")
        except Exception as e:
            print(f"Warning: Could not save plan file: {e}")
        
        # Count total items in plan
        total_items = sum(len(week_items) for week_items in weekly_plan.values())
        
        # Calculate total time commitment
        total_time = 0
        for week_items in weekly_plan.values():
            for item in week_items:
                if get_media_time_estimate:
                    total_time += get_media_time_estimate(item.get('type', 'art'))
                else:
                    total_time += 2  # Default 2 hours per item
        
        print(f"Generated 3-month plan: {total_items} items, {total_time} hours total")
        
        return {
            "success": True,
            "plan_items": total_items,
            "total_time_hours": total_time,
            "weeks": 12,
            "plan_file": plan_filename,
            "weekly_plan": weekly_plan
        }
        
    except Exception as e:
        print(f"Error generating 3-month plan: {e}")
        return {"success": False, "error": str(e)}

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

    try:
        # After 5 swipes, use personalized recommendations
        if right_swipes >= 5:
            print(f"Using personalized recommendations for user {user_uuid} (right swipes: {right_swipes})")
            personalized_candidates = get_personalized_candidates(user_uuid, limit=10)
            return {"candidates": personalized_candidates, "training_complete": False}
        else:
            # Use original logic for first 5 swipes
            print(f"Using original recommendations for user {user_uuid} (right swipes: {right_swipes})")
            user_items = get_user_items(user_uuid)
            candidate_ids = [ui["item_id"] for ui in user_items if ui["status"] == "candidate"]
            candidates = []
            for item_id in candidate_ids:
                item = get_item(item_id)
                if item:
                    candidates.append(item)
            return {"candidates": candidates, "training_complete": False}
    except Exception as e:
        print(f"Error getting personalized candidates: {e}")
        # Fallback to original logic
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
    
    # Update user embedding and trigger plan generation after 5 total swipes
    try:
        right_swipes = count_right_swipes(req.user_uuid)
        total_swipes = len([ui for ui in get_user_items(req.user_uuid) 
                           if ui["status"] in ["swipe_left", "swipe_right"]])
        
        # After exactly 5 total swipes, update embedding and trigger plan generation
        if total_swipes == 5:
            print(f"User {req.user_uuid} completed 5 swipes - updating embedding and generating 3-month plan")
            
            # Update user embedding based on swipe feedback
            update_user_embedding_from_swipes(req.user_uuid)
            
            # Get top-ranked remaining candidates for plan_agent
            personalized_candidates = get_personalized_candidates(req.user_uuid, limit=50)
            
            # Trigger plan generation
            plan_result = generate_three_month_plan(req.user_uuid, personalized_candidates)
            
            return {
                "success": True, 
                "training_complete": False,
                "swipes_complete": True,
                "plan_generated": plan_result.get("success", False),
                "plan_items": plan_result.get("plan_items", 0)
            }
            
        # Update embedding after every additional 5 swipes for continuous learning
        elif total_swipes > 5 and total_swipes % 5 == 0:
            print(f"Updating user embedding for {req.user_uuid} after {total_swipes} swipes")
            update_user_embedding_from_swipes(req.user_uuid)
            
    except Exception as e:
        print(f"Error updating user embedding or generating plan: {e}")
        # Continue even if embedding update fails
    
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
    # Generate and store user embedding
    user_embedding = generate_user_embedding(user_uuid, store_in_db=True)
    # Retrieve candidates from all domains
    movie_candidates = retrieve_top_candidates("movies", user_embedding, user_profile)
    book_candidates = retrieve_top_candidates("books", user_embedding, user_profile)
    music_candidates = retrieve_top_candidates("music", user_embedding, user_profile)
    art_candidates = retrieve_top_candidates("art", user_embedding, user_profile)
    poetry_candidates = retrieve_top_candidates("poetry", user_embedding, user_profile)
    podcast_candidates = retrieve_top_candidates("podcasts", user_embedding, user_profile)
    musical_candidates = retrieve_top_candidates("musicals", user_embedding, user_profile)
    # Merge and enrich with embeddings (stored in database)
    top_candidates = movie_candidates + book_candidates + music_candidates + art_candidates + poetry_candidates + podcast_candidates + musical_candidates
    top_candidates = batch_generate_embeddings(top_candidates, store_in_db=True)
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

@app.get("/api/user_plan/{user_uuid}")
def get_user_plan(user_uuid: str):
    """Get the user's 3-month plan if it exists."""
    try:
        plan_filename = f"user_plan_{user_uuid}.json"
        plan_filepath = os.path.join(os.path.dirname(__file__), "..", "plan_agent", plan_filename)
        
        if not os.path.exists(plan_filepath):
            return {"plan_exists": False, "message": "No plan generated yet"}
        
        with open(plan_filepath, 'r', encoding='utf-8') as f:
            weekly_plan = json.load(f)
        
        # Calculate plan statistics
        total_items = sum(len(week_items) for week_items in weekly_plan.values())
        total_time = 0
        for week_items in weekly_plan.values():
            for item in week_items:
                if get_media_time_estimate:
                    total_time += get_media_time_estimate(item.get('type', 'art'))
                else:
                    total_time += 2
        
        return {
            "plan_exists": True,
            "weekly_plan": weekly_plan,
            "statistics": {
                "total_items": total_items,
                "total_time_hours": total_time,
                "weeks": len(weekly_plan),
                "avg_hours_per_week": total_time / len(weekly_plan) if weekly_plan else 0
            }
        }
        
    except Exception as e:
        return {"plan_exists": False, "error": str(e)} 