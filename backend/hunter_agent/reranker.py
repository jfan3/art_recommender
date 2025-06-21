# tools/reranker.py
import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity

def update_user_embedding(user_embedding: List[float], feedback: List[int], candidate_embeddings: List[List[float]]) -> List[float]:
    """
    Update user embedding based on positive feedback.
    feedback: list of 1 (like) or 0 (dislike)
    candidate_embeddings: list of embeddings corresponding to candidates
    """
    user_vector = np.array(user_embedding)
    for i, signal in enumerate(feedback):
        if signal == 1:
            user_vector += 0.1 * np.array(candidate_embeddings[i])  # reinforcement
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