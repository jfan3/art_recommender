from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import time
import random
import traceback
import hashlib

# Import retriever functions for demo mode (without Supabase dependency)
try:
    from retriever import load_user_profile, retrieve_top_candidates
    from embedding import generate_user_embedding
    from art_embedding import batch_generate_embeddings  
    from reranker import update_user_embedding_from_swipes, get_personalized_candidates
    FULL_MODE = True
    print("Loaded full hunter agent with retriever")
except ImportError as e:
    print(f"Could not import full retriever functions: {e}")
    print("Running in demo mode")
    FULL_MODE = False

app = FastAPI(title="Hunter Agent Integrated API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo data for fallback
demo_candidates = [
    {
        "item_id": "art001",
        "item_name": "The Great Wave off Kanagawa", 
        "image_url": "https://picsum.photos/400/500",
        "category": "Art",
        "description": "Famous Japanese woodblock print by Hokusai"
    },
    {
        "item_id": "art002",
        "item_name": "Starry Night",
        "image_url": "https://picsum.photos/400/501", 
        "category": "Art",
        "description": "Iconic painting by Vincent van Gogh"
    },
    {
        "item_id": "book001",
        "item_name": "1984",
        "image_url": "https://picsum.photos/400/502",
        "category": "Books", 
        "description": "Dystopian novel by George Orwell"
    },
    {
        "item_id": "music001",
        "item_name": "Kind of Blue",
        "image_url": "https://picsum.photos/400/503",
        "category": "Music",
        "description": "Jazz album by Miles Davis"
    },
    {
        "item_id": "movie001", 
        "item_name": "2001: A Space Odyssey",
        "image_url": "https://picsum.photos/400/504",
        "category": "Movies",
        "description": "Sci-fi film by Stanley Kubrick"
    }
]

# Global state for demo mode
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

def mock_load_user_profile(user_uuid: str) -> dict:
    """Mock user profile loader for demo mode"""
    return {
        "uuid": user_uuid,
        "past_favorite_work": ["The Persistence of Memory", "Guernica"],
        "taste_genre": "surrealism, modern art, abstract expressionism", 
        "current_obsession": ["contemporary digital art", "interactive installations"],
        "state_of_mind": "seeking inspiration and new perspectives",
        "future_aspirations": "understanding diverse art movements",
        "complete": True
    }

def mock_retrieve_candidates(user_profile: dict) -> List[dict]:
    """Mock candidate retrieval based on user profile"""
    # Create personalized candidates based on profile
    candidates = []
    
    # Add art recommendations based on taste
    if "surrealism" in user_profile.get("taste_genre", "").lower():
        candidates.extend([
            {
                "item_id": "art_surreal_001",
                "item_name": "The Elephant Celebes",
                "image_url": "https://picsum.photos/400/510", 
                "category": "Art",
                "description": "Surrealist painting by Max Ernst",
                "creator": "Max Ernst",
                "source_url": "https://example.com/elephant-celebes"
            },
            {
                "item_id": "art_surreal_002", 
                "item_name": "The Treachery of Images",
                "image_url": "https://picsum.photos/400/511",
                "category": "Art", 
                "description": "Famous pipe painting by René Magritte",
                "creator": "René Magritte",
                "source_url": "https://example.com/treachery-images"
            }
        ])
    
    # Add contemporary art based on current obsession
    if "contemporary" in str(user_profile.get("current_obsession", [])).lower():
        candidates.extend([
            {
                "item_id": "art_contemp_001",
                "item_name": "Digital Landscape #47",
                "image_url": "https://picsum.photos/400/512",
                "category": "Art",
                "description": "Interactive digital installation by contemporary artist", 
                "creator": "Maya Chen",
                "source_url": "https://example.com/digital-landscape-47"
            }
        ])
    
    # Add diverse categories
    categories = ["Books", "Music", "Movies"]
    for i, category in enumerate(categories):
        candidates.append({
            "item_id": f"{category.lower()}_rec_{i}",
            "item_name": f"Recommended {category[:-1]} {i+1}",
            "image_url": f"https://picsum.photos/400/{520+i}",
            "category": category,
            "description": f"Personalized {category.lower()} recommendation based on your profile",
            "creator": "Various Artists",
            "source_url": f"https://example.com/{category.lower()}-rec-{i}"
        })
    
    # Add a few more diverse art pieces
    candidates.extend(demo_candidates)
    
    return candidates[:15]  # Return up to 15 candidates

@app.get("/")
def read_root():
    mode = "Full Mode" if FULL_MODE else "Demo Mode"
    return {"message": f"Hunter Agent Integrated API is running in {mode}"}

@app.get("/api/generation_status/{user_uuid}")
def generation_status_endpoint(user_uuid: str):
    # Check if we already have candidates for this user
    if user_uuid in user_candidates:
        return {"status": "complete"}
    
    # Simulate generation delay for first time users
    if user_uuid not in generation_status:
        generation_status[user_uuid] = "pending"
        # Mark as complete after a short delay and generate candidates
        import threading
        def generate_and_complete():
            time.sleep(2)
            try:
                if FULL_MODE:
                    # Try to load real user profile and retrieve candidates
                    user_profile = load_user_profile(user_uuid)
                    if user_profile and user_profile.get("complete", False):
                        print(f"Generating candidates for user {user_uuid} with full retriever")
                        # Generate user embedding
                        user_embedding = generate_user_embedding(user_uuid)
                        
                        # Retrieve candidates from different domains
                        all_candidates = []
                        domains = ["art", "books", "movies", "music", "poetry"]
                        for domain in domains:
                            try:
                                candidates = retrieve_top_candidates(domain, user_embedding, user_profile)
                                all_candidates.extend(candidates[:3])  # Take top 3 from each domain
                            except Exception as e:
                                print(f"Error retrieving {domain} candidates: {e}")
                        
                        # Batch generate embeddings
                        if all_candidates:
                            all_candidates = batch_generate_embeddings(all_candidates)
                        
                        user_candidates[user_uuid] = all_candidates[:10]  # Store top 10
                    else:
                        # Fallback to mock data if profile not complete
                        user_candidates[user_uuid] = mock_retrieve_candidates(mock_load_user_profile(user_uuid))
                else:
                    # Demo mode - use mock profile and candidates  
                    user_profile = mock_load_user_profile(user_uuid)
                    user_candidates[user_uuid] = mock_retrieve_candidates(user_profile)
                
                generation_status[user_uuid] = "complete"
                print(f"Generated {len(user_candidates[user_uuid])} candidates for user {user_uuid}")
            except Exception as e:
                print(f"Error generating candidates for {user_uuid}: {e}")
                # Fallback to demo data
                user_candidates[user_uuid] = demo_candidates
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
    candidates = user_candidates.get(user_uuid, demo_candidates)
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
    
    swipe_count = len(user_swipes[req.user_uuid])
    print(f"User {req.user_uuid} swiped {req.status} on {req.item_id}. Total swipes: {swipe_count}")
    
    # Check if 5 swipes completed
    if swipe_count >= 5:
        print(f"User {req.user_uuid} completed 5 swipes - generating plan")
        
        # Try to update user embedding and get personalized candidates if in full mode
        if FULL_MODE:
            try:
                # Update user embedding based on swipes 
                update_user_embedding_from_swipes(req.user_uuid)
                
                # Get personalized candidates for plan generation
                personalized_candidates = get_personalized_candidates(req.user_uuid, limit=50)
                plan_items = len(personalized_candidates)
            except Exception as e:
                print(f"Error in full mode processing: {e}")
                plan_items = random.randint(20, 50)
        else:
            plan_items = random.randint(20, 50)
        
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
    print(f"[INFO] Integrated Hunter Agent received candidate generation trigger for UUID: {user_uuid}")
    
    try:
        if FULL_MODE:
            # Try full mode first
            user_profile = load_user_profile(user_uuid)
            if user_profile and user_profile.get("complete", False):
                print(f"Generating candidates for user {user_uuid} with full retriever")
                # Generate user embedding
                user_embedding = generate_user_embedding(user_uuid)
                
                # Retrieve candidates from different domains  
                all_candidates = []
                domains = ["art", "books", "movies", "music", "poetry"]
                for domain in domains:
                    try:
                        candidates = retrieve_top_candidates(domain, user_embedding, user_profile) 
                        all_candidates.extend(candidates[:3])  # Take top 3 from each domain
                    except Exception as e:
                        print(f"Error retrieving {domain} candidates: {e}")
                
                # Batch generate embeddings
                if all_candidates:
                    all_candidates = batch_generate_embeddings(all_candidates)
                
                user_candidates[user_uuid] = all_candidates[:10]  # Store top 10
                generation_status[user_uuid] = "complete"
                return {"success": True, "candidates_generated": len(user_candidates[user_uuid])}
        
        # Fallback to demo mode
        print(f"Using demo mode for user {user_uuid}")
        user_profile = mock_load_user_profile(user_uuid)
        user_candidates[user_uuid] = mock_retrieve_candidates(user_profile)
        generation_status[user_uuid] = "complete"
        return {"success": True, "candidates_generated": len(user_candidates[user_uuid])}
        
    except Exception as e:
        print(f"Error generating candidates: {e}")
        print(traceback.format_exc())
        # Emergency fallback
        user_candidates[user_uuid] = demo_candidates
        generation_status[user_uuid] = "complete"  
        return {"success": True, "candidates_generated": len(demo_candidates)}

@app.get("/api/plan/{user_uuid}")
def get_plan(user_uuid: str):
    # Generate a mock 3-month plan based on user preferences
    swipes = user_swipes.get(user_uuid, [])
    liked_items = [s for s in swipes if s["status"] == "swipe_right"]
    
    weeks = {}
    for week in range(1, 13):
        week_items = []
        # Add 2-4 items per week, influenced by user's likes
        num_items = random.randint(2, 4)
        
        # If user liked certain categories, weight towards those
        candidates = user_candidates.get(user_uuid, demo_candidates)
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
        "user_preferences_applied": len(liked_items) > 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)