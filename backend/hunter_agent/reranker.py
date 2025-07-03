# tools/reranker.py
import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
from backend.db.supabase_client import (
    get_user_embedding, upsert_user_embedding, get_user_items, 
    get_items_with_embeddings
)

def update_user_embedding(user_embedding: List[float], feedback: List[int], candidate_embeddings: List[List[float]]) -> List[float]:
    """
    Update user embedding based on positive feedback.
    feedback: list of 1 (like) or 0 (dislike)
    candidate_embeddings: list of embeddings corresponding to candidates
    """
    user_vector = np.array(user_embedding)
    for i, signal in enumerate(feedback):
        if signal == 1:
            user_vector += 0.1 * np.array(candidate_embeddings[i])  # reinforce
        elif signal == 0:
            user_vector -= 0.05 * np.array(candidate_embeddings[i])  # discourage
    return (user_vector / np.linalg.norm(user_vector)).tolist()

def rerank_candidates(user_embedding: List[float], candidates: List[Dict], feedback: List[int]) -> List[Dict]:
    """
    Rerank candidates based on updated embedding.
    Each candidate should contain 'embedding' key.
    """
    updated_embedding = update_user_embedding(user_embedding, feedback, [c['embedding'] for c in candidates])
    similarities = cosine_similarity([updated_embedding], [c['embedding'] for c in candidates])[0]
    
    # Attach scores and sort
    for i, c in enumerate(candidates):
        c['score'] = similarities[i]
    
    return sorted(candidates, key=lambda x: x['score'], reverse=True)

def update_user_embedding_from_swipes(user_uuid: str) -> List[float]:
    """
    Update user embedding based on swipe history from database.
    Returns the updated embedding.
    """
    # Get current user embedding
    user_embedding_data = get_user_embedding(user_uuid)
    if not user_embedding_data:
        raise ValueError(f"No user embedding found for {user_uuid}")
    
    current_embedding = user_embedding_data["embedding"]
    current_version = user_embedding_data.get("version", 1)
    
    # Get user's swipe history
    user_items = get_user_items(user_uuid)
    
    # Separate liked and disliked items
    liked_items = [ui for ui in user_items if ui["status"] == "swipe_right"]
    disliked_items = [ui for ui in user_items if ui["status"] == "swipe_left"]
    
    # Get embeddings for liked and disliked items
    liked_item_ids = [ui["item_id"] for ui in liked_items]
    disliked_item_ids = [ui["item_id"] for ui in disliked_items]
    
    liked_embeddings = []
    disliked_embeddings = []
    
    if liked_item_ids:
        liked_items_with_embeddings = get_items_with_embeddings(liked_item_ids)
        liked_embeddings = [item["embedding"] for item in liked_items_with_embeddings]
    
    if disliked_item_ids:
        disliked_items_with_embeddings = get_items_with_embeddings(disliked_item_ids)
        disliked_embeddings = [item["embedding"] for item in disliked_items_with_embeddings]
    
    # Update embedding based on feedback
    user_vector = np.array(current_embedding)
    
    # Reinforce with liked items
    for embedding in liked_embeddings:
        user_vector += 0.1 * np.array(embedding)
    
    # Discourage with disliked items  
    for embedding in disliked_embeddings:
        user_vector -= 0.05 * np.array(embedding)
    
    # Normalize the updated embedding
    updated_embedding = (user_vector / np.linalg.norm(user_vector)).tolist()
    
    # Store updated embedding with incremented version
    upsert_user_embedding(user_uuid, updated_embedding, current_version + 1)
    
    print(f"Updated user embedding for {user_uuid} (version {current_version + 1})")
    return updated_embedding

def get_personalized_candidates(user_uuid: str, limit: int = 10) -> List[Dict]:
    """
    Get personalized candidate recommendations based on current user embedding.
    """
    # Get updated user embedding
    user_embedding_data = get_user_embedding(user_uuid)
    if not user_embedding_data:
        raise ValueError(f"No user embedding found for {user_uuid}")
    
    user_embedding = user_embedding_data["embedding"]
    
    # Get candidate items that haven't been swiped yet
    user_items = get_user_items(user_uuid)
    candidate_items = [ui for ui in user_items if ui["status"] == "candidate"]
    candidate_item_ids = [ui["item_id"] for ui in candidate_items]
    
    if not candidate_item_ids:
        return []
    
    # Get items with embeddings
    items_with_embeddings = get_items_with_embeddings(candidate_item_ids)
    
    if not items_with_embeddings:
        return []
    
    # Calculate similarities
    item_embeddings = [item["embedding"] for item in items_with_embeddings]
    similarities = cosine_similarity([user_embedding], item_embeddings)[0]
    
    # Attach scores and sort
    for i, item in enumerate(items_with_embeddings):
        item["score"] = similarities[i]
    
    # Return top candidates sorted by similarity
    sorted_candidates = sorted(items_with_embeddings, key=lambda x: x["score"], reverse=True)
    return sorted_candidates[:limit] 