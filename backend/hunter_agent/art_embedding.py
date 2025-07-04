# tools/art_embedding.py
import openai
import os
from typing import List, Dict
from db.supabase_client import upsert_item_embedding, get_item_embedding
import hashlib

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_item_id(url: str) -> str:
    """Generate a consistent item_id from a URL using SHA-256."""
    hash_object = hashlib.sha256(url.encode())
    return hash_object.hexdigest()[:12]


def generate_text_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    response = openai.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding


def make_embedding_text(item: dict) -> str:
    parts = [
        item.get("title", ""),
        item.get("description", ""),
        f"By {item.get('creator', '')}" if item.get("creator") else "",
        f"Category: {item.get('category', '')}" if item.get("category") else "",
        f"Released: {item.get('release_date', '')}" if item.get("release_date") else "",
    ]
    metadata = item.get("metadata", {})
    if metadata:
        for k, v in metadata.items():
            if v:
                parts.append(f"{k}: {v}")
    return ". ".join([p for p in parts if p])


def batch_generate_embeddings(candidates: List[Dict], store_in_db: bool = True) -> List[Dict]:
    """
    Converts candidate items into embedding-enriched data using all available fields.
    No longer stores embeddings in database; always returns in-memory enriched candidates.
    """
    enriched_candidates = []
    for item in candidates:
        # Generate item_id consistently
        source_url = item.get("source_url", "")
        if not source_url:
            continue
        item_id = generate_item_id(source_url)
        # Always generate new embedding in-memory
        text = make_embedding_text(item)
        if not text:
            continue
        embedding = generate_text_embedding(text)
        enriched_item = item.copy()
        enriched_item["embedding"] = embedding
        enriched_item["item_id"] = item_id  # Ensure item_id is included
        enriched_candidates.append(enriched_item)
    return enriched_candidates 