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

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Try to import Supabase client
try:
    from db.supabase_client import (
        get_user_profile, get_user_items, get_item, 
        update_user_item_status, upsert_item, upsert_user_item, 
        set_user_profile_complete
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
    from main import generate_smart_weekly_plan, get_media_time_estimate
    PLAN_AGENT_AVAILABLE = True
    print("✅ Successfully imported plan_agent functions")
except ImportError as e:
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

def get_demo_candidates_based_on_profile(user_profile: dict) -> List[dict]:
    """Generate demo candidates based on user profile data."""
    candidates = []
    
    # Parse user preferences
    taste_genre = user_profile.get("taste_genre", "").lower()
    past_favorites = user_profile.get("past_favorite_work", [])
    current_obsession = user_profile.get("current_obsession", [])
    
    print(f"Generating candidates based on profile:")
    print(f"  - Taste genre: {taste_genre}")
    print(f"  - Past favorites: {past_favorites}")
    print(f"  - Current obsession: {current_obsession}")
    
    # Generate art recommendations based on taste
    if any(keyword in taste_genre for keyword in ["abstract", "modern", "contemporary"]):
        candidates.extend([
            {
                "item_id": "art_modern_001",
                "item_name": "Composition with Red Blue and Yellow",
                "image_url": "https://picsum.photos/400/510",
                "category": "Art",
                "description": "Abstract painting by Piet Mondrian",
                "creator": "Piet Mondrian",
                "source_url": "https://example.com/mondrian-composition"
            },
            {
                "item_id": "art_modern_002",
                "item_name": "The Weeping Woman", 
                "image_url": "https://picsum.photos/400/511",
                "category": "Art",
                "description": "Cubist painting by Pablo Picasso",
                "creator": "Pablo Picasso",
                "source_url": "https://example.com/weeping-woman"
            }
        ])
    
    if any(keyword in taste_genre for keyword in ["surreal", "dream", "fantasy"]):
        candidates.extend([
            {
                "item_id": "art_surreal_001",
                "item_name": "The Persistence of Memory",
                "image_url": "https://picsum.photos/400/512",
                "category": "Art",
                "description": "Surrealist masterpiece by Salvador Dalí",
                "creator": "Salvador Dalí",
                "source_url": "https://example.com/persistence-memory"
            }
        ])
    
    # Add diverse fallback recommendations
    fallback_candidates = [
        {
            "item_id": "movie_classic_001",
            "item_name": "8½",
            "image_url": "https://picsum.photos/400/540",
            "category": "Movies",
            "description": "Federico Fellini's surreal masterpiece",
            "creator": "Federico Fellini",
            "source_url": "https://example.com/8-and-half"
        },
        {
            "item_id": "book_classic_001",
            "item_name": "The Metamorphosis",
            "image_url": "https://picsum.photos/400/520",
            "category": "Books",
            "description": "Kafka's existential masterpiece",
            "creator": "Franz Kafka",
            "source_url": "https://example.com/metamorphosis"
        },
        {
            "item_id": "music_jazz_001",
            "item_name": "Kind of Blue",
            "image_url": "https://picsum.photos/400/530",
            "category": "Music",
            "description": "Legendary jazz album by Miles Davis",
            "creator": "Miles Davis",
            "source_url": "https://example.com/kind-of-blue"
        }
    ]
    
    candidates.extend(fallback_candidates)
    
    # Ensure we have at least 5 candidates
    while len(candidates) < 5:
        candidates.append({
            "item_id": f"default_{len(candidates)}",
            "item_name": f"Curated Recommendation {len(candidates)+1}",
            "image_url": f"https://picsum.photos/400/{560+len(candidates)}",
            "category": "Art",
            "description": "Personalized recommendation based on your profile",
            "creator": "Various Artists",
            "source_url": f"https://example.com/rec-{len(candidates)}"
        })
    
    return candidates[:10]

def generate_three_month_plan(user_uuid: str, personalized_candidates: list) -> dict:
    """Generate a 3-month plan using plan_agent with personalized candidates."""
    try:
        if not PLAN_AGENT_AVAILABLE or not generate_smart_weekly_plan:
            # Fallback to mock plan generation
            return generate_mock_plan(user_uuid, personalized_candidates)
        
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
        return generate_mock_plan(user_uuid, personalized_candidates)

def generate_mock_plan(user_uuid: str, candidates: list) -> dict:
    """Generate a mock 3-month plan when plan_agent is not available."""
    print(f"Generating mock plan for user {user_uuid}")
    
    if not candidates:
        candidates = get_demo_candidates_based_on_profile({})
    
    weeks = {}
    for week in range(1, 13):
        week_items = []
        num_items = random.randint(2, 4)
        
        selected_items = random.sample(candidates, min(num_items, len(candidates)))
        
        for item in selected_items:
            week_items.append({
                "title": item.get("item_name", item.get("title", "Unknown")),
                "type": item.get("category", "art").lower(),
                "description": item.get("description", ""),
                "image_url": item.get("image_url", ""),
                "category": item.get("category", "Art"),
                "creator": item.get("creator", "Unknown Artist")
            })
        
        weeks[f"Week {week}"] = week_items
    
    total_items = sum(len(items) for items in weeks.values())
    total_time = total_items * 2  # Estimate 2 hours per item
    
    return {
        "success": True,
        "plan_items": total_items,
        "total_time_hours": total_time,
        "weeks": 12,
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

@app.get("/api/candidates/{user_uuid}")
def get_candidates(user_uuid: str):
    """Get candidates for a user - prioritizes full Supabase workflow."""
    # Handle test users with demo data
    if user_uuid.startswith("test-"):
        demo_candidates = get_demo_candidates_based_on_profile({})
        return {"candidates": demo_candidates, "training_complete": False}
    
    if not SUPABASE_AVAILABLE:
        # Return demo candidates if Supabase is not available
        demo_candidates = get_demo_candidates_based_on_profile({})
        return {"candidates": demo_candidates, "training_complete": False}
    
    # Check if user has reached 30 right swipes (training complete)
    right_swipes = count_right_swipes(user_uuid)
    if right_swipes >= RIGHT_SWIPE_LIMIT:
        return {"candidates": [], "training_complete": True}

    try:
        # After 5 swipes, use personalized recommendations if retriever available
        if right_swipes >= SWIPE_COMPLETION_THRESHOLD and RETRIEVER_AVAILABLE:
            print(f"🎯 Using personalized recommendations for user {user_uuid} (right swipes: {right_swipes})")
            personalized_candidates = get_personalized_candidates(user_uuid, limit=10)
            return {"candidates": personalized_candidates, "training_complete": False}
        else:
            # Use candidates from database for first 5 swipes
            print(f"📋 Using database candidates for user {user_uuid} (right swipes: {right_swipes})")
            user_items = get_user_items(user_uuid)
            candidate_ids = [ui["item_id"] for ui in user_items if ui["status"] == "candidate"]
            candidates = []
            for item_id in candidate_ids:
                item = get_item(item_id)
                if item:
                    candidates.append(item)
            
            # If no candidates found, generate demo candidates
            if not candidates:
                print(f"📦 No candidates in database, using demo candidates for {user_uuid}")
                try:
                    user_profile = get_user_profile(user_uuid) if SUPABASE_AVAILABLE else {}
                    candidates = get_demo_candidates_based_on_profile(user_profile or {})
                except:
                    candidates = get_demo_candidates_based_on_profile({})
            
            return {"candidates": candidates, "training_complete": False}
            
    except Exception as e:
        print(f"❌ Error getting candidates: {e}")
        print(traceback.format_exc())
        # Return demo candidates on error
        demo_candidates = get_demo_candidates_based_on_profile({})
        return {"candidates": demo_candidates, "training_complete": False}

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
    
    # Default to pending
    return {"status": "pending"}

@app.post("/api/generate_candidates/{user_uuid}")
def generate_candidates(user_uuid: str, request: Request):
    """Generate candidates for a user - requires full Supabase + retriever workflow."""
    print(f"🚀 Hunter Agent received candidate generation trigger for UUID: {user_uuid}")
    
    if not SUPABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Supabase connection required for candidate generation")
    
    if not RETRIEVER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Retriever functions required for candidate generation")
    
    try:
        generation_status[user_uuid] = "pending"
        
        # Load user profile from Supabase
        user_profile = load_user_profile(user_uuid)
        if not user_profile or user_profile.get("uuid") != user_uuid:
            print(f"❌ No user profile found for UUID: {user_uuid}")
            generation_status[user_uuid] = "error"
            raise HTTPException(status_code=404, detail="User profile not found or does not match")
        
        print(f"✅ Loaded user profile: {user_profile.get('taste_genre', 'No genre specified')}")
        
        # Generate user embedding (without storing to database)
        user_embedding = generate_user_embedding(user_uuid, store_in_db=False)
        print(f"✅ Generated user embedding for {user_uuid}")
        
        # Retrieve candidates from all content domains
        all_candidates = []
        for domain in CONTENT_DOMAINS:
            try:
                domain_candidates = retrieve_top_candidates(domain, user_embedding, user_profile)
                all_candidates.extend(domain_candidates)
                print(f"✅ Retrieved {len(domain_candidates)} {domain} candidates")
            except Exception as e:
                print(f"❌ Error retrieving {domain} candidates: {e}")
        
        if not all_candidates:
            raise HTTPException(status_code=500, detail="No candidates could be retrieved from any domain")
        
        # Batch generate embeddings (without storing to database)
        print(f"🔄 Generating embeddings for {len(all_candidates)} candidates")
        top_candidates = batch_generate_embeddings(all_candidates, store_in_db=False)
        
        # Store candidates and user_items in Supabase
        stored_count = 0
        for candidate in top_candidates:
            try:
                item_id = generate_item_id(candidate.get("source_url", candidate.get("title", "")))
                
                # Store item data
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
                
                # Store user-item relationship
                user_item_data = {
                    "uuid": user_uuid,
                    "item_id": item_id,
                    "status": "candidate"
                }
                upsert_user_item(user_item_data)
                stored_count += 1
                
            except Exception as e:
                print(f"❌ Error storing candidate {candidate.get('title', 'Unknown')}: {e}")
        
        # Mark profile as complete and update status
        set_user_profile_complete(user_uuid)
        generation_status[user_uuid] = "complete"
        
        print(f"✅ Hunter Agent finished candidate generation for {user_uuid}: {stored_count} candidates stored")
        return {"success": True, "candidates_generated": stored_count}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating candidates: {e}")
        print(traceback.format_exc())
        generation_status[user_uuid] = "error"
        raise HTTPException(status_code=500, detail=f"Error generating candidates: {str(e)}")

@app.get("/api/user_plan/{user_uuid}")
def get_user_plan(user_uuid: str):
    """Get the user's 3-month plan if it exists."""
    try:
        # Try to load plan from file first (if plan_agent was used)
        plan_filename = f"user_plan_{user_uuid}.json"
        plan_filepath = os.path.join(os.path.dirname(__file__), "..", "plan_agent", plan_filename)
        
        if os.path.exists(plan_filepath):
            with open(plan_filepath, 'r', encoding='utf-8') as f:
                weekly_plan = json.load(f)
            
            # Calculate plan statistics
            total_items = sum(len(week_items) for week_items in weekly_plan.values())
            total_time = 0
            for week_items in weekly_plan.values():
                for item in week_items:
                    if PLAN_AGENT_AVAILABLE and get_media_time_estimate:
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
                },
                "plan_type": "plan_agent"
            }
        
        # Fallback: generate plan from user's data
        if SUPABASE_AVAILABLE:
            print(f"📋 Generating plan from user data for {user_uuid}")
            
            # Get user profile and swipe history
            try:
                user_profile = get_user_profile(user_uuid) if hasattr(locals(), 'get_user_profile') else load_user_profile(user_uuid)
                user_items = get_user_items(user_uuid)
                liked_items = [item for item in user_items if item.get("status") == "swipe_right"]
                
                # Generate mock plan based on actual user data
                mock_plan_result = generate_mock_plan(user_uuid, [])
                
                return {
                    "plan_exists": True,
                    "weekly_plan": mock_plan_result["weekly_plan"],
                    "statistics": {
                        "total_items": mock_plan_result["plan_items"],
                        "total_time_hours": mock_plan_result["total_time_hours"],
                        "weeks": mock_plan_result["weeks"],
                        "avg_hours_per_week": mock_plan_result["total_time_hours"] / mock_plan_result["weeks"]
                    },
                    "plan_type": "generated_from_data",
                    "user_preferences_applied": len(liked_items) > 0
                }
                
            except Exception as e:
                print(f"❌ Error generating plan from user data: {e}")
        
        return {"plan_exists": False, "message": "No plan generated yet"}
        
    except Exception as e:
        print(f"❌ Error retrieving user plan: {e}")
        return {"plan_exists": False, "error": str(e)}

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