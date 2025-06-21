# tools/retriever.py
import requests
import os
from typing import List, Dict

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def search_google(query: str, num_results: int = 10) -> List[Dict]:
    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "num": num_results,
        "api_key": SERPAPI_API_KEY
    }
    response = requests.get(url, params=params)
    results = response.json()
    return results.get("organic_results", [])

def retrieve_top_candidates(category: str, user_embedding: List[float]) -> List[Dict]:
    """
    Simulate a retrieval function using embedding-based similarity.
    For now, use a keyword-based search as placeholder.
    """
    if category == "movies":
        query = "artistic movies like Donnie Darko"
    elif category == "books":
        query = "books with love and peace themes"
    elif category == "music":
        query = "music albums similar to Donnie Darko atmosphere"
    elif category == "musicals":
        query = "artistic musical theatre recommendations"
    else:
        query = "artistic recommendations"

    results = search_google(query, num_results=10)
    # Add the category to each result so we can use it later.
    for item in results:
        item['category'] = category
    return results 