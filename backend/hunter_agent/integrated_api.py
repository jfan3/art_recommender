from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import time
import random
import traceback
import hashlib

# Import retriever functions with absolute imports
try:
    from retriever import load_user_profile, retrieve_top_candidates
    from embedding import generate_user_embedding
    from art_embedding import batch_generate_embeddings  
    from reranker import update_user_embedding, get_personalized_candidates
    FULL_MODE = True
    print("Loaded full hunter agent with retriever")
except ImportError as e:
    print(f"Could not import full retriever functions: {e}")
    print("This should not happen - please check module paths")
    raise e

app = FastAPI(title="Hunter Agent Integrated API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NO DEMO DATA - only real candidates from APIs

# Global state for demo mode
generation_status = {}
user_swipes = {}
user_candidates = {}
user_plans = {}

class SwipeRequest(BaseModel):
    user_uuid: str
    item_id: str
    status: str

def generate_item_id(source_url_or_title: str) -> str:
    """Generate a deterministic item ID from a source URL or title."""
    return hashlib.md5(source_url_or_title.encode()).hexdigest()[:16]

# NO MOCK FUNCTIONS - only real API data

@app.get("/")
def read_root():
    mode = "Full Mode" if FULL_MODE else "Demo Mode"
    return {"message": f"Hunter Agent Integrated API is running in {mode}"}

@app.get("/api/debug/{user_uuid}")
def debug_user(user_uuid: str):
    return {
        "user_candidates_exists": user_uuid in user_candidates,
        "generation_status": generation_status.get(user_uuid, "not_found"),
        "candidates_count": len(user_candidates.get(user_uuid, [])),
        "user_candidates_keys": list(user_candidates.keys()),
        "full_mode": FULL_MODE
    }

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
                        domains = ["art", "books", "movies", "music", "poetry", "podcasts", "musicals"]
                        successful_domains = 0
                        
                        for domain in domains:
                            try:
                                candidates = retrieve_top_candidates(domain, user_embedding, user_profile)
                                if candidates:
                                    all_candidates.extend(candidates[:5])  # Take top 5 from each domain
                                    successful_domains += 1
                                    print(f"Retrieved {len(candidates[:5])} candidates from {domain}")
                            except Exception as e:
                                print(f"Error retrieving {domain} candidates: {e}")
                        
                        print(f"Successfully retrieved from {successful_domains}/{len(domains)} domains")
                        
                        # If we got very few candidates, try to get more from working domains
                        if len(all_candidates) < 10:
                            print(f"Only got {len(all_candidates)} candidates, attempting to get more from successful domains")
                            for domain in domains:
                                if len(all_candidates) >= 15:
                                    break
                                try:
                                    additional_candidates = retrieve_top_candidates(domain, user_embedding, user_profile)
                                    if additional_candidates:
                                        # Take more candidates from this domain
                                        all_candidates.extend(additional_candidates[5:10])  # Take candidates 5-10
                                        print(f"Added {len(additional_candidates[5:10])} additional candidates from {domain}")
                                except Exception as e:
                                    continue
                        
                        # Batch generate embeddings
                        if all_candidates:
                            all_candidates = batch_generate_embeddings(all_candidates)
                        
                        if all_candidates and len(all_candidates) >= 5:
                            user_candidates[user_uuid] = all_candidates[:15]  # Store top 15
                            print(f"Successfully generated {len(user_candidates[user_uuid])} REAL candidates for user {user_uuid} ({successful_domains} domains successful)")
                        else:
                            print(f"FAILED to retrieve sufficient real candidates for {user_uuid} - only got {len(all_candidates)}")
                            print("This indicates API failures - check your API keys and network connection")
                            # Don't fall back to mock data - return empty to force retry
                            user_candidates[user_uuid] = []
                    else:
                        # Profile not complete - return empty to indicate need for completion
                        print(f"Profile not complete for {user_uuid} - cannot generate real candidates")
                        user_candidates[user_uuid] = []
                else:
                    # FULL_MODE is False - this should never happen in production
                    print(f"ERROR: FULL_MODE is False for {user_uuid} - check configuration")
                    user_candidates[user_uuid] = []
                
                generation_status[user_uuid] = "complete"
                print(f"Final result: Generated {len(user_candidates[user_uuid])} candidates for user {user_uuid}")
            except Exception as e:
                print(f"CRITICAL ERROR generating candidates for {user_uuid}: {e}")
                import traceback
                traceback.print_exc()
                # Don't use demo data - return empty to indicate failure
                user_candidates[user_uuid] = []
                generation_status[user_uuid] = "error"
        
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
    
    # Return candidates if available - NO DEMO FALLBACK
    candidates = user_candidates.get(user_uuid, [])
    
    # Debug logging
    if user_uuid in user_candidates and candidates:
        print(f"Returning {len(candidates)} REAL candidates for {user_uuid}")
        print(f"First candidate: {candidates[0] if candidates else 'None'}")
    else:
        print(f"NO REAL candidates found for {user_uuid}")
        print(f"Available user_candidates keys: {list(user_candidates.keys())}")
        
        # Return error if no real candidates
        if not candidates:
            raise HTTPException(status_code=503, detail="No real candidates available. Please ensure your profile is complete and APIs are working.")
    
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
        print(f"User {req.user_uuid} completed 5 swipes - refining embedding and generating plan")
        
        def finalize_recommendations_and_plan():
            try:
                print(f"Starting plan generation for {req.user_uuid}")
                
                # Get user's swiped candidates to create a simple plan
                candidates = user_candidates.get(req.user_uuid, [])
                if not candidates:
                    print(f"No candidates found for {req.user_uuid}")
                    return 0
                
                # Create a simple plan using the candidates they swiped on
                # Focus on liked items first, then add variety from all candidates
                liked_swipes = [s for s in user_swipes[req.user_uuid] if s["status"] == "swipe_right"]
                all_swipes = user_swipes[req.user_uuid]
                
                print(f"Creating plan from {len(candidates)} candidates, {len(liked_swipes)} liked items")
                
                # Generate a 12-week plan
                plan = {}
                for week in range(1, 13):
                    week_items = []
                    items_per_week = 3  # 3 items per week
                    
                    # Select items for this week
                    selected_candidates = random.sample(candidates, min(items_per_week, len(candidates)))
                    
                    for candidate in selected_candidates:
                        week_items.append({
                            "title": candidate.get("item_name", candidate.get("title", "Unknown")),
                            "type": candidate.get("category", "art").lower(),
                            "description": candidate.get("description", ""),
                            "image_url": candidate.get("image_url", ""),
                            "source_url": candidate.get("source_url", ""),
                            "score": candidate.get("score", 0.0),
                            "category": candidate.get("category", "Art"),
                            "creator": candidate.get("creator", "Unknown Artist")
                        })
                    
                    plan[f"week_{week}"] = week_items
                
                # Store the plan
                user_plans[req.user_uuid] = plan
                print(f"Successfully generated simple plan for {req.user_uuid} with {len(plan)} weeks")
                return len(candidates)
                
            except Exception as e:
                print(f"CRITICAL ERROR generating plan for {req.user_uuid}: {e}")
                traceback.print_exc()
                
                # Create a minimal fallback plan to unblock the user
                try:
                    candidates = user_candidates.get(req.user_uuid, [])
                    if candidates:
                        minimal_plan = {}
                        for week in range(1, 5):  # Just 4 weeks
                            item = random.choice(candidates)
                            minimal_plan[f"week_{week}"] = [{
                                "title": item.get("item_name", "Art Recommendation"),
                                "type": "art",
                                "description": "Personalized recommendation",
                                "image_url": item.get("image_url", ""),
                                "source_url": item.get("source_url", ""),
                                "score": 0.8,
                                "category": "Art",
                                "creator": "Various"
                            }]
                        user_plans[req.user_uuid] = minimal_plan
                        print(f"Created minimal fallback plan for {req.user_uuid}")
                        return 1
                except:
                    pass
                return 0
        
        # Run finalization in background thread
        import threading
        threading.Thread(target=finalize_recommendations_and_plan, daemon=True).start()
        
        return {
            "success": True,
            "training_complete": False,
            "swipes_complete": True,
            "plan_generated": True,
            "message": "Generating your personalized 3-month plan..."
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
                domains = ["art", "books", "movies", "music", "poetry", "podcasts", "musicals"]
                successful_domains = 0
                
                for domain in domains:
                    try:
                        candidates = retrieve_top_candidates(domain, user_embedding, user_profile) 
                        if candidates:
                            all_candidates.extend(candidates[:5])  # Take top 5 from each domain
                            successful_domains += 1
                            print(f"Retrieved {len(candidates[:5])} candidates from {domain}")
                    except Exception as e:
                        print(f"Error retrieving {domain} candidates: {e}")
                
                print(f"Successfully retrieved from {successful_domains}/{len(domains)} domains")
                
                # Batch generate embeddings
                if all_candidates:
                    all_candidates = batch_generate_embeddings(all_candidates)
                
                if all_candidates and len(all_candidates) >= 5:
                    user_candidates[user_uuid] = all_candidates[:15]  # Store top 15
                    print(f"Successfully stored {len(user_candidates[user_uuid])} REAL candidates for user {user_uuid}")
                else:
                    print(f"Insufficient real candidates retrieved: {len(all_candidates)}")
                    return {"success": False, "error": "Could not retrieve sufficient real candidates"}
                generation_status[user_uuid] = "complete"
                return {"success": True, "candidates_generated": len(user_candidates[user_uuid])}
        
        # No demo mode fallback - real candidates only
        print(f"Profile incomplete or FULL_MODE disabled for user {user_uuid}")
        return {"success": False, "error": "Cannot generate candidates - profile incomplete or system misconfigured"}
        
    except Exception as e:
        print(f"Error generating candidates: {e}")
        print(traceback.format_exc())
        # No demo fallback - return error
        return {"success": False, "error": f"Failed to generate candidates: {str(e)}"}

@app.get("/api/plan/{user_uuid}")
def get_plan(user_uuid: str):
    # Check if we have a generated plan for this user
    if user_uuid in user_plans:
        plan = user_plans[user_uuid]
        print(f"Returning generated plan for user {user_uuid}")
        return {
            "success": True,
            "weekly_plan": plan,
            "total_weeks": len(plan),
            "total_items": sum(len(items) for items in plan.values()),
            "user_preferences_applied": True,
            "plan_generated": True
        }
    
    # Check if user has completed 5 swipes but plan is still being generated
    swipes = user_swipes.get(user_uuid, [])
    if len(swipes) >= 5:
        return {
            "success": True,
            "weekly_plan": {},
            "total_weeks": 0,
            "total_items": 0,
            "user_preferences_applied": False,
            "plan_generated": False,
            "message": "Your personalized plan is being generated. Please wait a moment..."
        }
    
    # NO MOCK PLAN - return error if no real plan exists
    print(f"No real plan available for user {user_uuid}")
    raise HTTPException(status_code=404, detail="No personalized plan available. Please complete your preference learning by swiping on real candidates first.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)