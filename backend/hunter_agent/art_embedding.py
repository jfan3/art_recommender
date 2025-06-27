# tools/embedding.py
import openai
import os
from typing import List, Dict

openai.api_key = os.getenv("OPENAI_API_KEY")


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


def batch_generate_embeddings(candidates: List[Dict]) -> List[Dict]:
    """
    Converts candidate items into embedding-enriched data using all available fields.
    """
    enriched_candidates = []
    for item in candidates:
        text = make_embedding_text(item)
        if not text:
            continue
        embedding = generate_text_embedding(text)
        enriched_item = item.copy()
        enriched_item["embedding"] = embedding
        enriched_candidates.append(enriched_item)
    return enriched_candidates 