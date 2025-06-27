# tools/retriever.py
import os
import json
import requests
import base64
from dotenv import load_dotenv  # pip install python-dotenv
from typing import List, Dict

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def load_user_profile(profile_path="art_recommender/user_profiles.json") -> dict:
    with open(profile_path, "r") as f:
        return json.load(f)

def build_query(category: str, profile: dict) -> str:
    taste = profile.get("taste_genre", "")
    favorites = ", ".join(profile.get("past_favorite_work", []))
    obsession = ", ".join(profile.get("current_obsession", []))
    state = profile.get("state_of_mind", "")
    if category == "movies":
        return f"{taste} movies like {favorites} and {obsession} {state}"
    elif category == "books":
        return f"{taste} books such as {favorites} and {obsession} {state}"
    elif category == "music":
        return f"{taste} music similar to {favorites} and {obsession} {state}"
    elif category == "musicals":
        return f"{taste} musical theatre recommendations {favorites} {obsession} {state}"
    else:
        return f"{taste} {category} recommendations {favorites} {obsession} {state}"

def search_openlibrary(query: str, num_results: int = 10) -> List[Dict]:
    url = "https://openlibrary.org/search.json"
    params = {"q": query, "limit": num_results}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = []
        for doc in data.get("docs", []):
            results.append({
                "title": doc.get("title"),
                "description": doc.get("first_sentence", {}).get("value", "") if doc.get("first_sentence") else "",
                "source_url": f"https://openlibrary.org{doc.get('key')}",
                "image_url": f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg" if doc.get("cover_i") else "",
                "type": "book",
                "category": "book",
                "creator": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                "release_date": doc.get("first_publish_year", ""),
                "metadata": {
                    "genre": ", ".join(doc.get("subject", [])) if doc.get("subject") else "",
                    "language": ", ".join(doc.get("language", [])) if doc.get("language") else "",
                    "country": doc.get("publish_country", ""),
                    "tags": ", ".join(doc.get("subject", [])) if doc.get("subject") else "",
                    "rating": doc.get("ratings_average", ""),
                    "awards": doc.get("awards", ""),
                }
            })
        return results
    else:
        print(f"[OpenLibrary] Error: {response.status_code}")
        return []

def search_google(query: str, num_results: int = 10) -> List[Dict]:
    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "num": num_results,
        "api_key": SERPAPI_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = []
        for item in data.get("organic_results", []):
            results.append({
                "title": item.get("title"),
                "description": item.get("snippet", ""),
                "source_url": item.get("link"),
                "image_url": item.get("thumbnail") or item.get("image", {}).get("src", ""),
                "type": "web",
                "category": "web",
                "creator": "",
                "release_date": "",
                "metadata": {
                    "displayed_link": item.get("displayed_link"),
                    "position": item.get("position"),
                    "tags": ", ".join(item.get("rich_snippet", {}).get("top", {}).get("tags", [])) if item.get("rich_snippet", {}).get("top", {}).get("tags") else "",
                    "rating": item.get("rating", ""),
                    "mood": item.get("mood", ""),
                }
            })
        return results
    else:
        print(f"[SerpAPI] Error: {response.status_code}")
        return []

def search_tmdb(query: str, num_results: int = 10) -> List[Dict]:
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "en-US",
        "page": 1,
        "include_adult": False
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = []
        for movie in data.get("results", [])[:num_results]:
            results.append({
                "title": movie.get("title"),
                "description": movie.get("overview", ""),
                "source_url": f"https://www.themoviedb.org/movie/{movie.get('id')}",
                "image_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else "",
                "type": "movie",
                "category": "movie",
                "creator": "",
                "release_date": movie.get("release_date", ""),
                "metadata": {
                    "original_language": movie.get("original_language", ""),
                    "genre": ", ".join([g["name"] for g in movie.get("genre_ids", [])]) if movie.get("genre_ids") else "",
                    "country": movie.get("origin_country", ""),
                    "rating": movie.get("vote_average", ""),
                    "tags": "",
                    "awards": "",
                }
            })
        return results
    else:
        print(f"[TMDB] Error: {response.status_code}")
        return []

def get_spotify_access_token() -> str:
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"[Spotify] Token Error: {response.status_code}", response.text)
        return None

def search_spotify(query: str, num_results: int = 10) -> List[Dict]:
    token = get_spotify_access_token()
    if not token:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "type": "track", "limit": num_results}
    response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        results = []
        for item in data.get("tracks", {}).get("items", []):
            album = item.get("album", {})
            results.append({
                "title": item.get("name"),
                "description": album.get("name", ""),
                "source_url": item.get("external_urls", {}).get("spotify", ""),
                "image_url": album.get("images", [{}])[0].get("url", ""),
                "type": "music",
                "category": "music",
                "creator": ", ".join([a["name"] for a in item.get("artists", [])]),
                "release_date": album.get("release_date", ""),
                "metadata": {
                    "genre": ", ".join(album.get("genres", [])) if album.get("genres") else "",
                    "tags": "",
                    "country": album.get("country", ""),
                    "language": album.get("languages", ""),
                    "rating": album.get("popularity", ""),
                    "mood": "",
                    "awards": "",
                }
            })
        return results
    else:
        print(f"[Spotify] Search Error: {response.status_code}", response.text)
        return []

def retrieve_top_candidates(category: str, user_embedding: List[float]) -> List[Dict]:
    profile = load_user_profile()
    query = build_query(category, profile)
    # Select the appropriate data source for each category
    if category == "books":
        results = search_openlibrary(query, num_results=20)
    elif category == "movies":
        results = search_tmdb(query, num_results=20)
    elif category == "musicals":
        results = search_google(query, num_results=20)
    elif category == "music":
        results = search_spotify(query, num_results=20)
    elif category == "art":
        results = search_google(query, num_results=20)
    elif category == "poetry":
        results = search_google(query, num_results=20)
    elif category == "podcasts":
        results = search_google(query, num_results=20)
    else:
        results = search_google(query, num_results=10)
    # Deduplicate results by title + source_url
    seen = set()
    unique_results = []
    for item in results:
        key = item.get("title", "") + item.get("source_url", "")
        if key not in seen:
            unique_results.append(item)
            seen.add(key)
    return unique_results[:100] 