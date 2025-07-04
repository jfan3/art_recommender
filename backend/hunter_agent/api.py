from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import json
import time
import random
import traceback
import hashlib
import importlib.util
from dotenv import load_dotenv
from reranker import get_personalized_candidates
from db.supabase_client import get_user_embedding, get_items_with_embeddings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables from .env file before any other imports
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Try to import Supabase client
try:
    from db.supabase_client import (
        get_user_profile, get_user_items, get_item, 
        update_user_item_status, upsert_item, upsert_user_item, 
        set_user_profile_complete, upsert_user_plan, get_user_plan as get_user_plan_from_db
    )
    SUPABASE_AVAILABLE = True
    print("✅ Successfully connected to Supabase")
except ImportError as e:
    print(f"❌ Could not import Supabase client: {e}")
    SUPABASE_AVAILABLE = False

# Try to import retriever functions
try:
    from .retriever import load_user_profile, retrieve_top_candidates
    from .embedding import generate_user_embedding
    from .art_embedding import batch_generate_embeddings
    from .reranker import update_user_embedding_from_swipes, get_personalized_candidates
    RETRIEVER_AVAILABLE = True
    print("✅ Successfully loaded retriever functions")
except ImportError:
    try:
        # Fallback to absolute imports
        from retriever import load_user_profile, retrieve_top_candidates
        from embedding import generate_user_embedding
        from art_embedding import batch_generate_embeddings
        from reranker import update_user_embedding_from_swipes, get_personalized_candidates
        RETRIEVER_AVAILABLE = True
        print("✅ Successfully loaded retriever functions")
    except ImportError as e:
        print(f"❌ Could not import retriever functions: {e}")
        RETRIEVER_AVAILABLE = False

# Try to import plan_agent functions
plan_agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plan_agent')
if plan_agent_path not in sys.path:
    sys.path.append(plan_agent_path)

try:
    plan_agent_main_path = os.path.join(plan_agent_path, 'main.py')
    spec = importlib.util.spec_from_file_location("plan_agent_main", plan_agent_main_path)
    plan_agent_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plan_agent_module)
    
    generate_smart_weekly_plan = plan_agent_module.generate_smart_weekly_plan
    get_media_time_estimate = plan_agent_module.get_media_time_estimate
    PLAN_AGENT_AVAILABLE = True
    print("✅ Successfully imported plan_agent functions")
except Exception as e:
    print(f"❌ Could not import plan_agent functions: {e}")
    generate_smart_weekly_plan = None
    get_media_time_estimate = None
    PLAN_AGENT_AVAILABLE = False

# Global state management
generation_status = {}
user_swipes = {}
user_candidates = {}

# Configuration constants
CONTENT_DOMAINS = ["art", "books", "movies", "music", "poetry", "podcasts", "musicals"]
SWIPE_COMPLETION_THRESHOLD = 5
RIGHT_SWIPE_LIMIT = 30

def generate_item_id(url: str) -> str:
    """Generate a consistent item_id from a URL using SHA-256."""
    hash_object = hashlib.sha256(url.encode())
    return hash_object.hexdigest()[:12]

def count_right_swipes(user_uuid: str) -> int:
    """Count how many right swipes a user has made."""
    if SUPABASE_AVAILABLE:
        try:
            user_items = get_user_items(user_uuid)
            return sum(1 for item in user_items if item["status"] == "swipe_right")
        except Exception as e:
            print(f"Error counting right swipes from Supabase: {e}")
    
    # Fallback to local tracking
    swipes = user_swipes.get(user_uuid, [])
    return sum(1 for swipe in swipes if swipe["status"] == "swipe_right")

def adjust_plan_for_preferences(base_plan: dict, duration: int, intensity: str) -> dict:
    """Adjust the base plan based on duration and intensity preferences."""
    max_weeks = duration * 4  # 4 weeks per month
    
    # Filter plan to only include the specified duration
    filtered_plan = {}
    for i in range(1, max_weeks + 1):
        week_key = f"week_{i}"
        if week_key in base_plan:
            week_items = base_plan[week_key]
            
            # Adjust items per week based on intensity (use fixed counts for consistency)
            intensity_target_items = {
                "chill": 2,
                "medium": 4, 
                "intense": 6
            }
            target_count = intensity_target_items.get(intensity, 4)
            
            if len(week_items) >= target_count:
                # Take exactly the target number
                adjusted_items = week_items[:target_count]
            elif len(week_items) > 0:
                # Pad with repeats to reach target count
                adjusted_items = week_items[:]
                while len(adjusted_items) < target_count:
                    adjusted_items.append(random.choice(week_items))
            else:
                # No items available
                adjusted_items = []
            
            filtered_plan[week_key] = adjusted_items
    
    return filtered_plan

# Demo candidates function removed - only real candidates from hunter_agent retriever

def generate_three_month_plan(user_uuid: str, personalized_candidates: list, duration_months: int = 3, intensity: str = "medium") -> dict:
    """Generate a flexible plan using plan_agent with personalized candidates.
    
    Args:
        user_uuid: User's UUID
        personalized_candidates: List of personalized candidates
        duration_months: Plan duration in months (1, 2, or 3)
        intensity: Plan intensity ("chill", "medium", or "intense")
    """
    try:
        if not PLAN_AGENT_AVAILABLE or not generate_smart_weekly_plan:
            # Fallback to mock plan generation
            return generate_mock_plan(user_uuid, personalized_candidates, duration_months, intensity)
        
        if not personalized_candidates:
            return {"success": False, "error": "No personalized candidates available"}
        
        # Format candidates for plan_agent
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
        
        # Calculate number of weeks based on duration
        num_weeks = duration_months * 4
        
        # Map intensity to effort level
        effort_map = {
            "chill": "low",
            "medium": "medium", 
            "intense": "high"
        }
        effort_level = effort_map.get(intensity, "medium")
        
        print(f"Generating {duration_months}-month plan for user {user_uuid} with {len(formatted_candidates)} candidates (intensity: {intensity})")
        weekly_plan = generate_smart_weekly_plan(formatted_candidates, num_weeks=num_weeks, effort_level=effort_level)
        
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
        
        # Also save plan to Supabase
        if SUPABASE_AVAILABLE:
            try:
                plan_data = {
                    "uuid": user_uuid,
                    "weekly_plan": weekly_plan,
                    "duration_months": duration_months,
                    "intensity": intensity,
                    "created_at": None  # Let Supabase set timestamp
                }
                upsert_user_plan(plan_data)
                print(f"✅ Saved plan to Supabase for user {user_uuid}")
            except Exception as e:
                print(f"❌ Could not save plan to Supabase: {e}")
        
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
            "weeks": num_weeks,
            "duration_months": duration_months,
            "intensity": intensity,
            "plan_file": plan_filename,
            "weekly_plan": weekly_plan
        }
        
    except Exception as e:
        print(f"Error generating 3-month plan: {e}")
        return generate_mock_plan(user_uuid, personalized_candidates, duration_months, intensity)

def generate_mock_plan(user_uuid: str, candidates: list, duration_months: int = 3, intensity: str = "medium") -> dict:
    """Generate a mock plan when plan_agent is not available."""
    print(f"Generating mock {duration_months}-month plan for user {user_uuid} (intensity: {intensity})")
    
    if not candidates:
        candidates = []
    
    # Calculate items per week based on intensity (fixed numbers for consistent totals)
    intensity_items = {
        "chill": 2,     # 2 items per week (relaxed pace)
        "medium": 4,    # 4 items per week (moderate pace)
        "intense": 6    # 6 items per week (intensive exploration)
    }
    items_per_week = intensity_items.get(intensity, 4)
    
    num_weeks = duration_months * 4
    weeks = {}
    
    for week in range(1, num_weeks + 1):
        week_items = []
        num_items = items_per_week
        
        # Ensure we always get exactly num_items by repeating candidates if needed
        for i in range(num_items):
            item = candidates[i % len(candidates)]  # Cycle through candidates
            week_items.append({
                "title": item.get("item_name", item.get("title", "Unknown")),
                "type": item.get("category", "art").lower(),
                "description": item.get("description", ""),
                "image_url": item.get("image_url", ""),
                "category": item.get("category", "Art"),
                "creator": item.get("creator", "Unknown Artist"),
                "score": item.get("score", random.uniform(0.7, 0.95))
            })
        
        weeks[f"week_{week}"] = week_items
    
    total_items = sum(len(items) for items in weeks.values())
    
    # Calculate time based on intensity (different time per item)
    time_per_item = {
        "chill": 1.5,    # 1.5 hours per item (leisurely pace)
        "medium": 2.0,   # 2 hours per item (standard pace)
        "intense": 2.5   # 2.5 hours per item (deep exploration)
    }
    hours_per_item = time_per_item.get(intensity, 2.0)
    total_time = round(total_items * hours_per_item, 2)
    
    # Debug logging
    expected_items = items_per_week * num_weeks
    expected_time = round(expected_items * hours_per_item, 2)
    print(f"📊 Plan calculation: {duration_months} months, {intensity} intensity")
    print(f"📊 Items per week: {items_per_week}, Total weeks: {num_weeks}")
    print(f"📊 Expected items: {expected_items}, Actual items: {total_items}")
    print(f"📊 Hours per item: {hours_per_item}")
    print(f"📊 Expected time: {expected_time}, Actual time: {total_time}")
    
    # Verify calculations match expectations
    if total_items != expected_items:
        print(f"⚠️ WARNING: Item count mismatch! Expected {expected_items}, got {total_items}")
    if total_time != expected_time:
        print(f"⚠️ WARNING: Time calculation mismatch! Expected {expected_time}, got {total_time}")
    
    # Save mock plan to Supabase (this will overwrite any existing plan)
    if SUPABASE_AVAILABLE:
        try:
            plan_data = {
                "uuid": user_uuid,
                "weekly_plan": weeks,
                "duration_months": duration_months,
                "intensity": intensity,
                "created_at": None  # Let Supabase set timestamp
            }
            upsert_user_plan(plan_data)
            print(f"✅ Saved mock plan to Supabase for user {user_uuid} ({duration_months} months, {intensity})")
        except Exception as e:
            print(f"❌ Could not save mock plan to Supabase: {e}")
    
    return {
        "success": True,
        "plan_items": total_items,
        "total_time_hours": total_time,
        "weeks": num_weeks,
        "duration_months": duration_months,
        "intensity": intensity,
        "plan_file": f"mock_plan_{user_uuid}.json",
        "weekly_plan": weeks
    }

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

class PlanGenerationRequest(BaseModel):
    user_uuid: str
    duration_months: int = 3  # 1, 2, or 3 months
    intensity: str = "medium"  # "chill", "medium", or "intense"

class PlanCustomizationRequest(BaseModel):
    user_uuid: str
    weekly_plan: dict  # Modified weekly plan from user
    confirmed: bool = False  # Whether user confirmed the plan

@app.get("/api/candidates/{user_uuid}")
def get_candidates(user_uuid: str):
    """
    Always use embedding-based ranking for candidates (in-memory, no DB embedding).
    - After 5 swipes: return top matches (personalized)
    - Before 5 swipes: return top N candidates by similarity
    - No fallback to static/prepared DB order
    """
    if not RETRIEVER_AVAILABLE:
        return {"candidates": [], "training_complete": False, "error": "Retriever required"}

    try:
        # 1. Ensure candidates are generated and cached
        if user_uuid not in user_candidates or not user_candidates[user_uuid]:
            return {"candidates": [], "training_complete": False, "error": "No candidates found. Please generate candidates first."}
        candidates = user_candidates[user_uuid]

        # 2. Get user profile and embedding
        user_profile = get_user_profile(user_uuid) if SUPABASE_AVAILABLE else None
        if not user_profile:
            return {"candidates": [], "training_complete": False, "error": "User profile not found"}
        from embedding import generate_user_embedding
        user_embedding = generate_user_embedding(user_profile, store_in_db=False)

        # 3. Generate item embeddings in-memory if not present
        from art_embedding import batch_generate_embeddings
        enriched_candidates = [c for c in candidates if c.get("embedding") is not None]
        if len(enriched_candidates) < len(candidates):
            # Some candidates missing embedding, regenerate all
            enriched_candidates = batch_generate_embeddings(candidates, store_in_db=False)
            user_candidates[user_uuid] = enriched_candidates  # update cache

        # 4. Compute similarities
        item_embeddings = [item["embedding"] for item in enriched_candidates]
        similarities = cosine_similarity([user_embedding], item_embeddings)[0]
        for i, item in enumerate(enriched_candidates):
            item["score"] = float(similarities[i])

        # 5. Sort by similarity
        sorted_candidates = sorted(enriched_candidates, key=lambda x: x["score"], reverse=True)

        # 6. Count swipes
        user_items = get_user_items(user_uuid) if SUPABASE_AVAILABLE else []
        user_swipes = [ui for ui in user_items if ui["status"] in ["swipe_left", "swipe_right"]]
        total_swipes = len(user_swipes)
        right_swipes = len([ui for ui in user_items if ui["status"] == "swipe_right"])

        # 7. After 5 swipes, return personalized (top 10)
        if total_swipes >= SWIPE_COMPLETION_THRESHOLD:
            return {"candidates": sorted_candidates[:10], "training_complete": False}
        else:
            # Before 5 swipes, return top N by similarity
            return {"candidates": sorted_candidates[:10], "training_complete": False}
    except Exception as e:
        print(f"❌ Error in in-memory candidate ranking: {e}")
        import traceback
        print(traceback.format_exc())
        return {"candidates": [], "training_complete": False, "error": str(e)}

@app.post("/api/swipe")
def swipe(req: SwipeRequest):
    """Process user swipe - stores in Supabase and updates embeddings."""
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Supabase connection required for full workflow")
    
    # Convert URL to item_id if a URL was passed
    item_id = req.item_id
    if item_id.startswith('http'):
        item_id = generate_item_id(item_id)
    
    try:
        # Update the user_item status in Supabase
        result = update_user_item_status(req.user_uuid, item_id, req.status)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update swipe status in database")
        
        print(f"✅ Saved swipe to Supabase: {req.user_uuid} {req.status} {item_id}")
        
        # Calculate current swipe counts from Supabase
        right_swipes = count_right_swipes(req.user_uuid)
        user_items = get_user_items(req.user_uuid)
        total_swipes = len([ui for ui in user_items if ui["status"] in ["swipe_left", "swipe_right"]])
        
        print(f"📊 User {req.user_uuid}: {total_swipes} total swipes, {right_swipes} right swipes")
        
        # After exactly 5 total swipes, update embedding and trigger plan generation
        if total_swipes == SWIPE_COMPLETION_THRESHOLD:
            print(f"🎉 User {req.user_uuid} completed {SWIPE_COMPLETION_THRESHOLD} swipes - updating embedding and generating plan")
            
            plan_items = 0
            if RETRIEVER_AVAILABLE:
                try:
                    # Update user embedding based on swipe feedback
                    update_user_embedding_from_swipes(req.user_uuid)
                    print(f"✅ Updated user embedding for {req.user_uuid}")
                    
                    # Get personalized candidates for plan generation
                    personalized_candidates = get_personalized_candidates(req.user_uuid, limit=50)
                    print(f"✅ Generated {len(personalized_candidates)} personalized candidates")
                    
                    # Trigger plan generation
                    plan_result = generate_three_month_plan(req.user_uuid, personalized_candidates)
                    plan_items = plan_result.get("plan_items", 0)
                    
                except Exception as e:
                    print(f"❌ Error in retriever workflow: {e}")
                    # Still generate a plan with available data
                    plan_result = generate_three_month_plan(req.user_uuid, [])
                    plan_items = plan_result.get("plan_items", 0)
            else:
                # Generate plan without retriever
                plan_result = generate_three_month_plan(req.user_uuid, [])
                plan_items = plan_result.get("plan_items", 0)
            
            return {
                "success": True, 
                "training_complete": False,
                "swipes_complete": True,
                "plan_generated": plan_result.get("success", False),
                "plan_items": plan_items
            }
            
        # Update embedding after every additional 5 swipes for continuous learning
        elif total_swipes > SWIPE_COMPLETION_THRESHOLD and total_swipes % 5 == 0 and RETRIEVER_AVAILABLE:
            try:
                print(f"🔄 Updating user embedding for {req.user_uuid} after {total_swipes} swipes")
                update_user_embedding_from_swipes(req.user_uuid)
            except Exception as e:
                print(f"❌ Error updating embedding: {e}")
        
        # Check if we've reached the right swipe limit (training complete)
        if req.status == "swipe_right" and right_swipes >= RIGHT_SWIPE_LIMIT:
            print(f"🏁 User {req.user_uuid} reached {RIGHT_SWIPE_LIMIT} right swipes - training complete")
            return {"success": True, "training_complete": True}
        
        return {"success": True, "training_complete": False}
        
    except Exception as e:
        print(f"❌ Error processing swipe: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing swipe: {str(e)}")

@app.get("/api/generation_status/{user_uuid}")
def get_generation_status(user_uuid: str):
    """Check if candidate generation is complete for a user."""
    # Check cached status first
    if user_uuid in generation_status:
        return {"status": generation_status[user_uuid]}
    
    # For test users, return complete immediately
    if user_uuid.startswith("test-"):
        generation_status[user_uuid] = "complete"
        return {"status": "complete"}
    
    # Check if user already has candidates in database
    if SUPABASE_AVAILABLE:
        try:
            user_items = get_user_items(user_uuid)
            if user_items and any(item["status"] == "candidate" for item in user_items):
                generation_status[user_uuid] = "complete"
                return {"status": "complete"}
        except Exception as e:
            print(f"Error checking user items: {e}")
    
    # Check if user has a completed profile to trigger generation
    if SUPABASE_AVAILABLE:
        try:
            user_profile = get_user_profile(user_uuid)
            if user_profile and user_profile.get("complete", False):
                # Profile is complete but no candidates yet - trigger generation
                generation_status[user_uuid] = "pending"
                # Start candidate generation in background
                import threading
                def generate_in_background():
                    try:
                        # Generate real candidates using hunter_agent retriever
                        if RETRIEVER_AVAILABLE:
                            user_embedding = generate_user_embedding(user_uuid, store_in_db=False)
                            all_candidates = []
                            domains = ["art", "books", "movies", "music", "poetry", "podcasts", "musicals"]
                            
                            for domain in domains:
                                try:
                                    domain_candidates = retrieve_top_candidates(domain, user_embedding, user_profile)
                                    all_candidates.extend(domain_candidates[:10])  # Take top 10 from each domain
                                    print(f"✅ Retrieved {len(domain_candidates)} {domain} candidates")
                                except Exception as e:
                                    print(f"❌ Error retrieving {domain} candidates: {e}")
                            
                            if all_candidates:
                                all_candidates = batch_generate_embeddings(all_candidates)
                                user_candidates[user_uuid] = all_candidates[:60]  # Return top 60 candidates
                                generation_status[user_uuid] = "complete"
                                print(f"✅ Generated {len(user_candidates[user_uuid])} real candidates for {user_uuid}")
                            else:
                                generation_status[user_uuid] = "error"
                                print(f"❌ No real candidates generated for {user_uuid}")
                        else:
                            generation_status[user_uuid] = "error"
                            print(f"❌ Retriever not available for {user_uuid}")
                    except Exception as e:
                        print(f"❌ Error generating candidates: {e}")
                        generation_status[user_uuid] = "error"
                
                threading.Thread(target=generate_in_background, daemon=True).start()
                return {"status": "pending"}
        except Exception as e:
            print(f"Error checking user profile: {e}")
    
    # Default to pending
    return {"status": "pending"}

@app.post("/api/generate_candidates/{user_uuid}")
def generate_candidates(user_uuid: str, request: Request):
    """
    Full workflow:
    1. Load user profile from Supabase
    2. Use retriever.py to dynamically generate candidates
    3. Store all candidates in Supabase (item, user_item as 'candidate')
    4. Generate user embedding in-memory (do not store in DB)
    5. Generate candidate embeddings in-memory (do not store in DB)
    6. Return success and number of candidates
    """
    print(f"🚀 [WORKFLOW] Generating candidates for user: {user_uuid}")
    if not SUPABASE_AVAILABLE or not RETRIEVER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Supabase and retriever required")
    try:
        # 1. Load user profile
        user_profile = get_user_profile(user_uuid)
        print(f"✅ Loaded user profile: {user_profile.get('art_category', 'N/A')}")
        # 2. Generate user embedding in-memory
        from embedding import generate_user_embedding
        user_embedding = generate_user_embedding(user_profile, store_in_db=False)
        print(f"✅ Generated user embedding in-memory for {user_uuid}")
        # 3. Use retriever to get candidates
        all_candidates = retrieve_top_candidates(user_embedding, user_profile)
        print(f"✅ Retrieved {len(all_candidates)} candidates")
        # 4. Upsert all candidates to item and user_item tables
        for candidate in all_candidates:
            if not candidate.get("item_id"):
                candidate["item_id"] = generate_item_id(candidate.get("source_url", candidate.get("title", "")))
            upsert_item({
                "item_id": candidate["item_id"],
                "item_name": candidate.get("item_name") or candidate.get("title", ""),
                "description": candidate.get("description", ""),
                "source_url": candidate.get("source_url", ""),
                "image_url": candidate.get("image_url", ""),
                "category": candidate.get("category", ""),
                "creator": candidate.get("creator", ""),
                "release_date": candidate.get("release_date", ""),
                "metadata": candidate.get("metadata", {})
            })
            upsert_user_item({
                "uuid": user_uuid,
                "item_id": candidate["item_id"],
                "status": "candidate"
            })
        print(f"✅ Stored {len(all_candidates)} candidates in Supabase (item + user_item)")
        # 5. Generate item embeddings in-memory (do not store in DB)
        from art_embedding import batch_generate_embeddings
        item_embeddings = batch_generate_embeddings(all_candidates, store_in_db=False)
        print(f"✅ Generated {len(item_embeddings)} item embeddings in-memory")
        # 6. Return success
        return {"success": True, "num_candidates": len(all_candidates)}
    except Exception as e:
        print(f"❌ Error in full candidate generation workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user_plan/{user_uuid}")
def get_user_plan(user_uuid: str, duration: int = 3, intensity: str = "medium"):
    """Get the user's plan with custom duration and intensity."""
    try:
        # First try to load plan from Supabase
        base_weekly_plan = None
        if SUPABASE_AVAILABLE:
            try:
                supabase_plan = get_user_plan_from_db(user_uuid)
                if supabase_plan and supabase_plan.get("weekly_plan"):
                    base_weekly_plan = supabase_plan["weekly_plan"]
                    print(f"✅ Loaded plan from Supabase for user {user_uuid}")
            except Exception as e:
                print(f"❌ Could not load plan from Supabase: {e}")
        
        # Fallback: Try to load base plan from file (if plan_agent was used)
        if not base_weekly_plan:
            plan_filename = f"user_plan_{user_uuid}.json"
            plan_filepath = os.path.join(os.path.dirname(__file__), "..", "plan_agent", plan_filename)
            
            if os.path.exists(plan_filepath):
                with open(plan_filepath, 'r', encoding='utf-8') as f:
                    base_weekly_plan = json.load(f)
                print(f"✅ Loaded plan from file for user {user_uuid}")
        
        # If we have a base plan, filter and adjust it based on duration and intensity
        if base_weekly_plan:
            weekly_plan = adjust_plan_for_preferences(base_weekly_plan, duration, intensity)
            
            # Calculate plan statistics with proper intensity-based time
            total_items = sum(len(week_items) for week_items in weekly_plan.values())
            
            # Use intensity-based time calculation (matching generate_mock_plan)
            time_per_item = {
                "chill": 1.5,    # 1.5 hours per item (leisurely pace)
                "medium": 2.0,   # 2 hours per item (standard pace)
                "intense": 2.5   # 2.5 hours per item (deep exploration)
            }
            hours_per_item = time_per_item.get(intensity, 2.0)
            
            total_time = 0
            for week_items in weekly_plan.values():
                for item in week_items:
                    if PLAN_AGENT_AVAILABLE and get_media_time_estimate:
                        total_time += get_media_time_estimate(item.get('type', 'art'))
                    else:
                        total_time += hours_per_item
            
            total_time = round(total_time, 2)
            
            return {
                "plan_exists": True,
                "weekly_plan": weekly_plan,
                "statistics": {
                    "total_items": total_items,
                    "total_time_hours": total_time,
                    "weeks": len(weekly_plan),
                    "avg_hours_per_week": round(total_time / len(weekly_plan), 1) if weekly_plan else 0
                },
                "plan_type": "plan_agent",
                "duration": duration,
                "intensity": intensity
            }
        
        # Fallback: generate plan from user's data or create new plan
        if SUPABASE_AVAILABLE:
            print(f"📋 Generating plan from user data for {user_uuid} (duration: {duration}, intensity: {intensity})")
            
            # Get user profile and swipe history
            try:
                user_profile = get_user_profile(user_uuid) if hasattr(locals(), 'get_user_profile') else load_user_profile(user_uuid)
                user_items = get_user_items(user_uuid)
                liked_items = [item for item in user_items if item.get("status") == "swipe_right"]
                
                # Generate mock plan based on actual user data with custom parameters
                mock_plan_result = generate_mock_plan(user_uuid, [], duration_months=duration, intensity=intensity)
                
                return {
                    "plan_exists": True,
                    "weekly_plan": mock_plan_result["weekly_plan"],
                    "statistics": {
                        "total_items": mock_plan_result["plan_items"],
                        "total_time_hours": mock_plan_result["total_time_hours"],
                        "weeks": mock_plan_result["weeks"],
                        "avg_hours_per_week": round(mock_plan_result["total_time_hours"] / mock_plan_result["weeks"], 1)
                    },
                    "plan_type": "generated_from_data",
                    "user_preferences_applied": len(liked_items) > 0,
                    "duration": duration,
                    "intensity": intensity
                }
                
            except Exception as e:
                print(f"❌ Error generating plan from user data: {e}")
        
        # Last resort: generate a basic plan even without Supabase
        print(f"📋 Generating basic plan for {user_uuid} (duration: {duration}, intensity: {intensity})")
        mock_plan_result = generate_mock_plan(user_uuid, [], duration_months=duration, intensity=intensity)
        
        return {
            "plan_exists": True,
            "weekly_plan": mock_plan_result["weekly_plan"],
            "statistics": {
                "total_items": mock_plan_result["plan_items"],
                "total_time_hours": mock_plan_result["total_time_hours"],
                "weeks": mock_plan_result["weeks"],
                "avg_hours_per_week": round(mock_plan_result["total_time_hours"] / mock_plan_result["weeks"], 1)
            },
            "plan_type": "basic_generated",
            "user_preferences_applied": False,
            "duration": duration,
            "intensity": intensity
        }
        
        return {"plan_exists": False, "message": "No plan generated yet"}
        
    except Exception as e:
        print(f"❌ Error retrieving user plan: {e}")
        return {"plan_exists": False, "error": str(e)}

@app.post("/api/generate_plan")
def generate_custom_plan(request: PlanGenerationRequest):
    """Generate a customized plan based on user preferences."""
    try:
        # Get user's personalized candidates
        if RETRIEVER_AVAILABLE and SUPABASE_AVAILABLE:
            personalized_candidates = get_personalized_candidates(request.user_uuid, limit=100)
        else:
            # Use demo candidates if retriever not available
            user_profile = get_user_profile(request.user_uuid) if SUPABASE_AVAILABLE else {}
            personalized_candidates = get_demo_candidates_based_on_profile(user_profile or {})
        
        # Generate plan with custom parameters
        plan_result = generate_three_month_plan(
            request.user_uuid, 
            personalized_candidates,
            duration_months=request.duration_months,
            intensity=request.intensity
        )
        
        return plan_result
        
    except Exception as e:
        print(f"Error generating custom plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customize_plan")
def customize_plan(request: PlanCustomizationRequest):
    """Save customized plan after user modifications."""
    try:
        # Save the customized plan
        plan_filename = f"user_plan_custom_{request.user_uuid}.json"
        plan_filepath = os.path.join(os.path.dirname(__file__), "..", "plan_agent", plan_filename)
        
        os.makedirs(os.path.dirname(plan_filepath), exist_ok=True)
        with open(plan_filepath, 'w', encoding='utf-8') as f:
            json.dump(request.weekly_plan, f, indent=2, ensure_ascii=False)
        
        # If confirmed, generate art journey photo
        if request.confirmed:
            # TODO: Implement art journey photo generation
            # For now, return success with placeholder
            return {
                "success": True,
                "plan_saved": True,
                "confirmed": True,
                "art_journey_url": f"https://example.com/art-journey/{request.user_uuid}.png",
                "message": "Plan saved and art journey generated!"
            }
        
        return {
            "success": True,
            "plan_saved": True,
            "confirmed": False,
            "message": "Plan saved successfully"
        }
        
    except Exception as e:
        print(f"Error customizing plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    """API status endpoint."""
    components = {
        "supabase": "✅ Connected" if SUPABASE_AVAILABLE else "❌ Unavailable",
        "retriever": "✅ Available" if RETRIEVER_AVAILABLE else "❌ Unavailable", 
        "plan_agent": "✅ Available" if PLAN_AGENT_AVAILABLE else "❌ Unavailable"
    }
    
    mode = "Full Workflow" if SUPABASE_AVAILABLE and RETRIEVER_AVAILABLE else "Limited Mode"
    
    return {
        "message": f"Hunter Agent Consolidated API - {mode}",
        "components": components,
        "workflow_mode": mode
    } 