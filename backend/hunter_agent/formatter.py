from typing import List, Dict

def format_for_user(raw_results: List[Dict]) -> List[Dict]:
    formatted = []
    for item in raw_results:
        formatted_item = {
            "title": item.get("title", ""),
            "type": item.get("type", ""),  # Use 'type' field from retriever
            "description": item.get("description", ""),  # Use 'description' field from retriever
            "source_url": item.get("source_url", ""),  # Use 'source_url' field from retriever
            "image_url": item.get("image_url", ""),  # Use 'image_url' field from retriever
            "creator": item.get("creator", ""),  # Add creator field
            "release_date": item.get("release_date", ""),  # Add release_date field
            "metadata": item.get("metadata", {})  # Use the full metadata from retriever
        }
        formatted.append(formatted_item)
    return formatted 