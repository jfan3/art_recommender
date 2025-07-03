from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import time
import random

app = FastAPI(title="Hunter Agent Demo API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo data
generation_status = {}
demo_candidates = [
    {
        "item_id": "test1",
        "item_name": "The Great Wave off Kanagawa",
        "image_url": "https://picsum.photos/400/500",
        "category": "Art",
        "description": "Famous Japanese woodblock print by Hokusai"
    },
    {
        "item_id": "test2", 
        "item_name": "Starry Night",
        "image_url": "https://picsum.photos/400/501",
        "category": "Art",
        "description": "Iconic painting by Vincent van Gogh"
    },
    {
        "item_id": "test3",
        "item_name": "Girl with a Pearl Earring", 
        "image_url": "https://picsum.photos/400/502",
        "category": "Art",
        "description": "Masterpiece by Johannes Vermeer"
    },
    {
        "item_id": "test4",
        "item_name": "The Scream",
        "image_url": "https://picsum.photos/400/503", 
        "category": "Art",
        "description": "Expressionist painting by Edvard Munch"
    },
    {
        "item_id": "test5",
        "item_name": "Guernica",
        "image_url": "https://picsum.photos/400/504",
        "category": "Art", 
        "description": "Anti-war painting by Pablo Picasso"
    }
]

user_swipes = {}

class SwipeRequest(BaseModel):
    user_uuid: str
    item_id: str
    status: str

@app.get("/")
def read_root():
    return {"message": "Hunter Agent Demo API is running"}

@app.get("/api/generation_status/{user_uuid}")
def generation_status_endpoint(user_uuid: str):
    # Simulate generation delay for first time users
    if user_uuid not in generation_status:
        generation_status[user_uuid] = "pending"
        # Mark as complete after a short delay
        import threading
        def mark_complete():
            time.sleep(2)
            generation_status[user_uuid] = "complete"
        threading.Thread(target=mark_complete, daemon=True).start()
    
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
    
    return {
        "candidates": demo_candidates,
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
    
    # Check if 5 swipes completed
    if swipe_count >= 5:
        return {
            "success": True,
            "training_complete": False,
            "swipes_complete": True,
            "plan_generated": True,
            "plan_items": random.randint(20, 50)
        }
    
    return {
        "success": True,
        "training_complete": False,
        "swipes_complete": False
    }

@app.post("/api/generate_candidates/{user_uuid}")
def generate_candidates(user_uuid: str, request: Request):
    print(f"[INFO] Demo Hunter Agent received candidate generation trigger for UUID: {user_uuid}")
    generation_status[user_uuid] = "complete"
    return {"success": True, "candidates_generated": len(demo_candidates)}

@app.get("/api/plan/{user_uuid}")
def get_plan(user_uuid: str):
    # Generate a mock 3-month plan
    weeks = {}
    for week in range(1, 13):
        week_items = []
        # Add 2-4 random items per week
        num_items = random.randint(2, 4)
        selected_items = random.sample(demo_candidates, min(num_items, len(demo_candidates)))
        
        for item in selected_items:
            week_items.append({
                "title": item["item_name"],
                "type": item["category"].lower(),
                "description": item["description"],
                "image_url": item["image_url"],
                "category": item["category"]
            })
        
        weeks[f"Week {week}"] = week_items
    
    return {
        "success": True,
        "weekly_plan": weeks,
        "total_weeks": 12,
        "total_items": sum(len(items) for items in weeks.values())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)