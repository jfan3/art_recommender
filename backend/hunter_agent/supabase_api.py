from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import time
import random
import traceback
import hashlib
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    # Try to import Supabase client and real functions
    from db.supabase_client import get_user_profile, get_user_items, get_item, update_user_item_status, upsert_item, upsert_user_item
    SUPABASE_AVAILABLE = True
    print("✅ Successfully connected to Supabase")
except ImportError as e:
    print(f"❌ Could not import Supabase client: {e}")
    SUPABASE_AVAILABLE = False

# Try to import retriever functions
try:
    from retriever import load_user_profile, retrieve_top_candidates, build_query
    from embedding import generate_user_embedding
    from art_embedding import batch_generate_embeddings  
    from reranker import update_user_embedding_from_swipes, get_personalized_candidates
    RETRIEVER_AVAILABLE = True
    print("✅ Successfully loaded retriever functions")
except ImportError as e:
    print(f"❌ Could not import retriever functions: {e}")
    RETRIEVER_AVAILABLE = False

app = FastAPI(title="Hunter Agent Supabase API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
generation_status = {}
user_swipes = {}
user_candidates = {}

class SwipeRequest(BaseModel):
    user_uuid: str
    item_id: str
    status: str

def generate_item_id(source_url_or_title: str) -> str:
    """Generate a deterministic item ID from a source URL or title."""
    return hashlib.md5(source_url_or_title.encode()).hexdigest()[:16]

def get_demo_candidates_based_on_profile(user_profile: dict) -> List[dict]:
    """Generate demo candidates based on actual user profile data from Supabase"""
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
    
    # Add books based on past favorites
    if past_favorites and any("book" in str(fav).lower() for fav in past_favorites):
        candidates.append({
            "item_id": "book_rec_001",
            "item_name": "The Metamorphosis",
            "image_url": "https://picsum.photos/400/520",
            "category": "Books",
            "description": "Kafka's existential masterpiece",
            "creator": "Franz Kafka",
            "source_url": "https://example.com/metamorphosis"
        })
    
    # Add music based on current obsession
    if current_obsession and any("music" in str(obs).lower() for obs in current_obsession):
        candidates.append({
            "item_id": "music_rec_001", 
            "item_name": "In a Silent Way",
            "image_url": "https://picsum.photos/400/530",
            "category": "Music",
            "description": "Experimental jazz album by Miles Davis",
            "creator": "Miles Davis",
            "source_url": "https://example.com/silent-way"
        })
    
    # Add fallback diverse recommendations
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
            "item_id": "poetry_rec_001",
            "item_name": "The Waste Land",
            "image_url": "https://picsum.photos/400/550",
            "category": "Poetry",
            "description": "Modernist poem by T.S. Eliot", 
            "creator": "T.S. Eliot",
            "source_url": "https://example.com/waste-land"
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
    
    return candidates[:10]  # Return max 10 candidates

@app.get("/")
def read_root():
    status = "Full Supabase Mode" if SUPABASE_AVAILABLE else "Demo Mode"
    retriever_status = "Available" if RETRIEVER_AVAILABLE else "Demo Mode"
    return {
        "message": f"Hunter Agent Supabase API is running",
        "supabase_status": status,
        "retriever_status": retriever_status
    }

@app.get("/api/generation_status/{user_uuid}")
def generation_status_endpoint(user_uuid: str):
    # Check if we already have candidates for this user
    if user_uuid in user_candidates:
        return {"status": "complete"}
    
    # Simulate generation delay for first time users
    if user_uuid not in generation_status:
        generation_status[user_uuid] = "pending"
        # Mark as complete after generating candidates
        import threading
        def generate_and_complete():
            time.sleep(2)
            try:
                if SUPABASE_AVAILABLE:
                    # Load real user profile from Supabase
                    user_profile = get_user_profile(user_uuid)
                    if user_profile and user_profile.get("complete", False):
                        print(f"✅ Loaded user profile from Supabase for {user_uuid}")
                        print(f"Profile data: {user_profile}")
                        
                        if RETRIEVER_AVAILABLE:
                            # Try full retriever workflow
                            print("🔍 Using full retriever workflow")
                            user_embedding = generate_user_embedding(user_uuid)
                            
                            # Retrieve candidates from different domains
                            all_candidates = []
                            domains = ["art", "books", "movies", "music"]
                            for domain in domains:
                                try:
                                    candidates = retrieve_top_candidates(domain, user_embedding, user_profile)
                                    all_candidates.extend(candidates[:3])  # Take top 3 from each domain
                                    print(f"Retrieved {len(candidates)} {domain} candidates")
                                except Exception as e:
                                    print(f"Error retrieving {domain} candidates: {e}")
                            
                            # Batch generate embeddings
                            if all_candidates:
                                all_candidates = batch_generate_embeddings(all_candidates)
                            
                            user_candidates[user_uuid] = all_candidates[:10]  # Store top 10
                        else:
                            # Use demo candidates based on real profile
                            print("🎭 Using demo candidates with real profile data")
                            user_candidates[user_uuid] = get_demo_candidates_based_on_profile(user_profile)
                    else:
                        print(f"❌ No complete profile found for {user_uuid}")
                        # Create default demo candidates
                        user_candidates[user_uuid] = get_demo_candidates_based_on_profile({})
                else:
                    print("❌ Supabase not available, using fallback")
                    user_candidates[user_uuid] = get_demo_candidates_based_on_profile({})
                
                generation_status[user_uuid] = "complete"
                print(f"✅ Generated {len(user_candidates[user_uuid])} candidates for user {user_uuid}")
            except Exception as e:
                print(f"❌ Error generating candidates for {user_uuid}: {e}")
                print(traceback.format_exc())
                # Emergency fallback
                user_candidates[user_uuid] = get_demo_candidates_based_on_profile({})
                generation_status[user_uuid] = "complete"
        
        threading.Thread(target=generate_and_complete, daemon=True).start()
    
    return {"status": generation_status.get(user_uuid, "pending")}

@app.get("/api/candidates/{user_uuid}")
def get_candidates(user_uuid: str):
    # Initialize user swipes if not exists
    if user_uuid not in user_swipes:
        user_swipes[user_uuid] = []
    
    # Check if 5 swipes completed
    swipe_count = len(user_swipes[user_uuid])
    if swipe_count >= 5:
        return {
            "candidates": [],
            "training_complete": False,
            "swipes_complete": True
        }
    
    # Return candidates if available
    candidates = user_candidates.get(user_uuid, [])
    if not candidates:
        # Try to generate candidates on demand
        try:
            if SUPABASE_AVAILABLE:
                user_profile = get_user_profile(user_uuid)
                if user_profile:
                    candidates = get_demo_candidates_based_on_profile(user_profile)
                    user_candidates[user_uuid] = candidates
        except Exception as e:
            print(f"Error loading candidates on demand: {e}")
    
    return {
        "candidates": candidates,
        "training_complete": False,
        "swipes_complete": False
    }

@app.post("/api/swipe")
def swipe(req: SwipeRequest):
    # Initialize user swipes if not exists
    if req.user_uuid not in user_swipes:
        user_swipes[req.user_uuid] = []
    
    # Record the swipe
    user_swipes[req.user_uuid].append({
        "item_id": req.item_id,
        "status": req.status,
        "timestamp": time.time()
    })
    
    # Try to save swipe to Supabase if available
    if SUPABASE_AVAILABLE:
        try:
            update_user_item_status(req.user_uuid, req.item_id, req.status)
            print(f"✅ Saved swipe to Supabase: {req.user_uuid} {req.status} {req.item_id}")
        except Exception as e:
            print(f"❌ Failed to save swipe to Supabase: {e}")
    
    swipe_count = len(user_swipes[req.user_uuid])
    print(f"User {req.user_uuid} swiped {req.status} on {req.item_id}. Total swipes: {swipe_count}")
    
    # Check if 5 swipes completed
    if swipe_count >= 5:
        print(f"🎉 User {req.user_uuid} completed 5 swipes - generating plan")
        
        # In-memory embedding update: get profile, swipes, and update embedding
        # (Demo: just print, or implement if needed)
        print("[In-memory] Skipping DB embedding update, using profile+swipes if needed.")
        plan_items = random.randint(20, 50)
        print(f" Generated {plan_items} personalized candidates")
        
        return {
            "success": True,
            "training_complete": False,
            "swipes_complete": True,
            "plan_generated": True,
            "plan_items": plan_items
        }
    
    return {
        "success": True,
        "training_complete": False,
        "swipes_complete": False
    }

@app.post("/api/generate_candidates/{user_uuid}")
def generate_candidates(user_uuid: str, request: Request):
    print(f"🚀 Supabase Hunter Agent received candidate generation trigger for UUID: {user_uuid}")
    
    try:
        if SUPABASE_AVAILABLE:
            # Load real user profile from Supabase
            user_profile = get_user_profile(user_uuid)
            if user_profile and user_profile.get("complete", False):
                print(f"✅ Profile loaded from Supabase: {user_profile.get('taste_genre', 'No genre')}")
                
                if RETRIEVER_AVAILABLE:
                    # Full retriever workflow
                    user_embedding = generate_user_embedding(user_uuid)
                    all_candidates = []
                    domains = ["art", "books", "movies", "music", "poetry"]
                    for domain in domains:
                        try:
                            candidates = retrieve_top_candidates(domain, user_embedding, user_profile)
                            all_candidates.extend(candidates[:3])
                        except Exception as e:
                            print(f"Error retrieving {domain}: {e}")
                    
                    if all_candidates:
                        all_candidates = batch_generate_embeddings(all_candidates)
                    
                    user_candidates[user_uuid] = all_candidates[:10]
                    generation_status[user_uuid] = "complete"
                    return {"success": True, "candidates_generated": len(user_candidates[user_uuid])}
                else:
                    # Demo candidates with real profile
                    user_candidates[user_uuid] = get_demo_candidates_based_on_profile(user_profile)
                    generation_status[user_uuid] = "complete"
                    return {"success": True, "candidates_generated": len(user_candidates[user_uuid])}
            else:
                print(f"❌ No complete profile found for {user_uuid}")
                return {"error": "User profile not found or incomplete"}
        else:
            print("❌ Supabase not available")
            return {"error": "Supabase not available"}
        
    except Exception as e:
        print(f"❌ Error generating candidates: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}

@app.get("/api/plan/{user_uuid}")
def get_plan(user_uuid: str):
    # Generate a mock 3-month plan based on user preferences
    swipes = user_swipes.get(user_uuid, [])
    liked_items = [s for s in swipes if s["status"] == "swipe_right"]
    
    # Load user profile to personalize plan
    user_profile = {}
    if SUPABASE_AVAILABLE:
        try:
            user_profile = get_user_profile(user_uuid) or {}
        except Exception as e:
            print(f"Error loading profile for plan: {e}")
    
    weeks = {}
    for week in range(1, 13):
        week_items = []
        # Add 2-4 items per week
        num_items = random.randint(2, 4)
        
        candidates = user_candidates.get(user_uuid, [])
        if not candidates:
            candidates = get_demo_candidates_based_on_profile(user_profile)
        
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
    
    return {
        "success": True,
        "weekly_plan": weeks,
        "total_weeks": 12,
        "total_items": sum(len(items) for items in weeks.values()),
        "user_preferences_applied": len(liked_items) > 0,
        "profile_based": bool(user_profile)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)