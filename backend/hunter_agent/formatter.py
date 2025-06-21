from typing import List, Dict

def format_for_user(raw_results: List[Dict]) -> List[Dict]:
    formatted = []
    for item in raw_results:
        formatted_item = {
            "title": item.get("title"),
            "type": item.get("category"),  # Read category from the item itself.
            "description": item.get("snippet", ""),
            "source_url": item.get("link"),
            "image_url": item.get("thumbnail") or item.get("image", {}).get("src", ""),
            "metadata": {
                "source": item.get("displayed_link"),
                "position": item.get("position")
            }
        }
        formatted.append(formatted_item)
    return formatted 