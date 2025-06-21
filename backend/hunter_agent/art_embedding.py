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


def batch_generate_embeddings(candidates: List[Dict], text_field: str = "title") -> List[Dict]:
    """
    Converts candidate items into embedding-enriched data.
    """
    enriched_candidates = []
    for item in candidates:
        text = item.get(text_field, "")
        if not text:
            continue
        embedding = generate_text_embedding(text)
        enriched_item = item.copy()
        enriched_item["embedding"] = embedding
        enriched_candidates.append(enriched_item)
    return enriched_candidates 