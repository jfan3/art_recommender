# tools/retriever.py
import os
import json
import requests
import base64
from dotenv import load_dotenv  # pip install python-dotenv
from typing import List, Dict
from datetime import datetime

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def load_user_profile(profile_path="art_recommender/user_profiles.json") -> dict:
    with open(profile_path, "r") as f:
        data = json.load(f)
    
    # Handle the format where user_profiles.json contains a dict with UUID keys
    if isinstance(data, dict) and len(data) > 0:
        # Get the first user profile
        first_uuid = list(data.keys())[0]
        profile = data[first_uuid]
        print(f"Loaded profile for UUID: {first_uuid}")
    else:
        # Fallback to direct profile format
        profile = data
    
    # Map actual field names to expected field names
    field_mapping = {
        "favorite_taste_genre_description": "taste_genre",
        "current_state_of_mind": "state_of_mind"
    }
    
    # Apply field mapping
    for actual_field, expected_field in field_mapping.items():
        if actual_field in profile and expected_field not in profile:
            profile[expected_field] = profile[actual_field]
    
    # Validate required fields exist
    required_fields = ["past_favorite_work", "taste_genre", "current_obsession", "state_of_mind", "future_aspirations"]
    for field in required_fields:
        if field not in profile:
            print(f"Warning: Missing required field '{field}' in user profile")
            profile[field] = "" if field != "past_favorite_work" and field != "current_obsession" else []
    
    # Handle new fields with defaults
    if "uuid" not in profile:
        profile["uuid"] = ""
    if "complete" not in profile:
        profile["complete"] = False
    if "created_at" not in profile:
        profile["created_at"] = ""
    if "updated_at" not in profile:
        profile["updated_at"] = ""
    
    return profile

def build_query(category: str, profile: dict) -> str:
    taste = profile.get("taste_genre", "").strip()
    favorites = ", ".join([f.strip() for f in profile.get("past_favorite_work", []) if f.strip()])
    obsession = ", ".join([o.strip() for o in profile.get("current_obsession", []) if o.strip()])
    state = profile.get("state_of_mind", "").strip()
    
    # Add profile completion context
    profile_status = "complete profile" if profile.get("complete", False) else "developing profile"
    
    # For APIs like TMDB and OpenLibrary, use the simplest possible queries
    if category in ["movies", "books"]:
        # Use only the most relevant content for better API results
        if favorites:
            return favorites  # Just use the favorite work name
        elif taste:
            return taste  # Fallback to taste genre
        else:
            return category  # Last resort
    else:
        # For web search APIs, use more detailed queries
        components = []
        
        if taste:
            components.append(taste)
        
        if category == "music":
            components.extend(["music"])
            if favorites:
                components.extend(["similar to", favorites])
            if obsession:
                components.extend(["and", obsession])
        elif category == "musicals":
            # More specific musical theatre search
            components.extend(["musical", "Broadway", "West End", "recommendations"])
            
            # Only include taste genre if it's not too specific
            if taste and len(taste) < 30:
                components.append(taste)
            
            if obsession:
                components.append(obsession)
            
            # Add specific musical terms
            components.extend(["musical", "theatre", "stage"])
        elif category == "art":
            # More specific art search
            components.extend(["contemporary art", "artists"])
            if favorites:
                components.append(favorites)
            if obsession:
                components.append(obsession)
            components.extend(["exhibitions", "galleries"])
        elif category == "poetry":
            # More specific poetry search
            components.extend(["poetry", "poets"])
            if favorites:
                components.append(favorites)
            if obsession:
                components.append(obsession)
            components.extend(["contemporary", "poems"])
        elif category == "podcasts":
            # More specific podcast search
            components.extend(["podcasts"])
            if favorites:
                components.append(favorites)
            if obsession:
                components.append(obsession)
            components.extend(["audio", "storytelling"])
        else:
            components.extend([category, "recommendations"])
            if favorites:
                components.append(favorites)
            if obsession:
                components.append(obsession)
        
        if state:
            components.append(state)
        
        # Add profile status for web searches
        components.append(profile_status)
        
        # Join components and clean up extra whitespace
        query = " ".join(components)
        query = " ".join(query.split())  # Remove extra whitespace
        
        return query

def search_openlibrary(query: str, num_results: int = 10) -> List[Dict]:
    url = "https://openlibrary.org/search.json"
    params = {"q": query, "limit": num_results}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = []
        for doc in data.get("docs", []):
            results.append({
                "title": doc.get("title") or "",
                "description": (doc.get("first_sentence", {}) or {}).get("value", "") if doc.get("first_sentence") else "",
                "source_url": f"https://openlibrary.org{doc.get('key') or ''}",
                "image_url": f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg" if doc.get("cover_i") else "",
                "type": "book",
                "category": "book",
                "creator": ", ".join(doc.get("author_name", []) or []) or "",
                "release_date": str(doc.get("first_publish_year") or ""),
                "metadata": {
                    "genre": ", ".join(doc.get("subject", []) or []) or "",
                    "language": ", ".join(doc.get("language", []) or []) or "",
                    "country": doc.get("publish_country") or "",
                    "tags": ", ".join(doc.get("subject", []) or []) or "",
                    "rating": str(doc.get("ratings_average") or ""),
                    "awards": doc.get("awards") or "",
                }
            })
        return results
    else:
        print(f"[OpenLibrary] Error: {response.status_code}")
        return []

def search_google(query: str, num_results: int = 10, category: str = "general") -> List[Dict]:
    url = "https://serpapi.com/search.json"
    
    # Define high-quality sites for different categories
    quality_sites = {
        "art": [
            "artsy.net", "artnet.com", "theartstory.org", "tate.org.uk", 
            "moma.org", "metmuseum.org", "guggenheim.org", "whitney.org",
            "saatchiart.com", "artforum.com", "hyperallergic.com",
            "artnews.com", "artspace.com", "artbasel.com", "frieze.com",
            "contemporaryartdaily.com", "e-flux.com", "art-agenda.com"
        ],
        "poetry": [
            "poetryfoundation.org", "poets.org", "poetryarchive.org", 
            "poetrysociety.org.uk", "poetryinternational.org", "poetry.com",
            "poetryoutloud.org", "poetryproject.org", "poetrymagazine.org",
            "poetrysociety.org", "poetrylondon.co.uk", "poetryireland.ie",
            "poetrynz.org.nz", "poetry.org.au", "poetrycanada.ca"
        ],
        "musicals": [
            "broadway.com", "playbill.com", "broadwayworld.com", 
            "tonyawards.com", "musicalschwartz.com", "mtishows.com",
            "rnh.com", "broadwayleague.com", "newyorktheatreguide.com",
            "londontheatre.co.uk", "whatsonstage.com", "theatremonkey.com",
            "westendtheatre.com", "musicaltheatreinternational.com"
        ],
        "podcasts": [
            "spotify.com", "apple.com", "npr.org", "bbc.co.uk", 
            "radiolab.org", "thisamericanlife.org", "ted.com",
            "wondery.com", "gimletmedia.com", "serialpodcast.org",
            "gimletmedia.com", "earwolf.com", "maximumfun.org",
            "stitcher.com", "audible.com", "anchor.fm"
        ]
    }
    
    # Enhanced query construction with category-specific keywords
    category_keywords = {
        "art": "contemporary art exhibitions galleries museums artists",
        "poetry": "contemporary poetry poets poems literary",
        "musicals": "musical theatre Broadway West End stage",
        "podcasts": "podcast audio storytelling radio"
    }
    
    # Build enhanced query with site restrictions and category keywords
    sites = quality_sites.get(category, [])
    category_kw = category_keywords.get(category, "")
    
    if sites:
        site_filter = " OR ".join([f"site:{site}" for site in sites])
        enhanced_query = f"({query}) ({category_kw}) ({site_filter})"
    else:
        enhanced_query = f"({query}) ({category_kw})"
    
    # Add negative keywords to filter out low-quality sites and non-content pages
    negative_keywords = [
        "-site:quora.com", "-site:reddit.com", "-site:youtube.com",
        "-site:facebook.com", "-site:twitter.com", "-site:instagram.com",
        "-site:linkedin.com", "-site:pinterest.com", "-site:tumblr.com",
        "-site:wikipedia.org", "-site:answers.com", "-site:yahoo.com",
        "-site:ask.com", "-site:stackoverflow.com", "-site:medium.com",
        "-sitemap", "-site:map", "-site-map", "-sitemap.xml", "-robots.txt",
        "-privacy", "-terms", "-contact", "-about", "-help", "-faq"
    ]
    
    final_query = f"{enhanced_query} {' '.join(negative_keywords)}"
    
    params = {
        "q": final_query,
        "num": num_results * 3,  # Request more results to account for filtering
        "api_key": SERPAPI_API_KEY,
        "gl": "us",  # Geographic location
        "hl": "en",  # Language
        "safe": "active",  # Safe search
        "sort": "relevance"  # Sort by relevance
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = []
        
        for item in data.get("organic_results", []):
            link = item.get("link", "")
            title = item.get("title", "")
            description = item.get("snippet", "")
            
            # Skip low-quality sites
            low_quality_domains = [
                "quora.com", "reddit.com", "youtube.com", "facebook.com",
                "twitter.com", "instagram.com", "linkedin.com", "pinterest.com",
                "tumblr.com", "wikipedia.org", "answers.com", "yahoo.com",
                "ask.com", "stackoverflow.com", "medium.com", "blogspot.com",
                "wordpress.com", "weebly.com", "squarespace.com"
            ]
            
            if any(domain in link.lower() for domain in low_quality_domains):
                continue
            
            # Skip if title or description is too short
            if len(title) < 10 or len(description) < 20:
                continue
            
            # Skip if title contains unwanted keywords
            unwanted_keywords = ["quora", "reddit", "youtube", "facebook", "twitter"]
            if any(keyword in title.lower() for keyword in unwanted_keywords):
                continue
            
            # Skip sitemaps and other non-content pages
            sitemap_keywords = ["sitemap", "site map", "site-map", "robots.txt", "privacy", "terms", "contact", "about", "help", "faq"]
            if any(keyword in title.lower() for keyword in sitemap_keywords):
                continue
            
            # Skip if URL contains sitemap patterns (but be less strict)
            if "/sitemap" in link.lower() and "sitemap" in title.lower():
                continue
            
            # Extract domain for metadata
            domain = ""
            try:
                domain = link.split("/")[2] if len(link.split("/")) > 2 else ""
            except:
                domain = ""
            
            results.append({
                "title": title,
                "description": description,
                "source_url": link,
                "image_url": item.get("thumbnail") or (item.get("image", {}) or {}).get("src", "") or "",
                "type": "web",
                "category": category,
                "creator": "",
                "release_date": "",
                "metadata": {
                    "displayed_link": item.get("displayed_link") or "",
                    "position": str(item.get("position") or ""),
                    "tags": ", ".join((item.get("rich_snippet", {}) or {}).get("top", {}).get("tags", []) or []) or "",
                    "rating": str(item.get("rating") or ""),
                    "mood": item.get("mood") or "",
                    "domain": domain,
                    "quality_score": "high" if domain in sites else "medium"
                }
            })
            
            # Stop if we have enough high-quality results
            if len(results) >= num_results:
                break
                
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
                "title": movie.get("title") or "",
                "description": movie.get("overview", "") or "",
                "source_url": f"https://www.themoviedb.org/movie/{movie.get('id') or ''}",
                "image_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path') or ''}" if movie.get("poster_path") else "",
                "type": "movie",
                "category": "movie",
                "creator": "",
                "release_date": movie.get("release_date") or "",
                "metadata": {
                    "original_language": movie.get("original_language") or "",
                    "genre": ", ".join([str(g) for g in movie.get("genre_ids", [])] if movie.get("genre_ids") else []) or "",
                    "country": movie.get("origin_country") or "",
                    "rating": str(movie.get("vote_average") or ""),
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
        return ""

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
            album = item.get("album", {}) or {}
            results.append({
                "title": item.get("name") or "",
                "description": album.get("name") or "",
                "source_url": item.get("external_urls", {}).get("spotify", "") or "",
                "image_url": (album.get("images", [{}]) or [{}])[0].get("url", "") or "",
                "type": "music",
                "category": "music",
                "creator": ", ".join([a["name"] for a in item.get("artists", [])] if item.get("artists") else []) or "",
                "release_date": album.get("release_date") or "",
                "metadata": {
                    "genre": ", ".join(album.get("genres", []) or []) or "",
                    "tags": "",
                    "country": album.get("country") or "",
                    "language": album.get("languages") or "",
                    "rating": str(album.get("popularity") or ""),
                    "mood": "",
                    "awards": "",
                }
            })
        return results
    else:
        print(f"[Spotify] Search Error: {response.status_code}", response.text)
        return []

def retrieve_top_candidates(category: str, user_embedding: List[float], user_profile: dict) -> List[Dict]:
    query = build_query(category, user_profile)
    # Select the appropriate data source for each category
    if category == "books":
        results = search_openlibrary(query, num_results=20)
    elif category == "movies":
        results = search_tmdb(query, num_results=20)
    elif category == "musicals":
        results = search_google(query, num_results=20, category="musicals")
    elif category == "music":
        results = search_spotify(query, num_results=20)
    elif category == "art":
        results = search_google(query, num_results=20, category="art")
    elif category == "poetry":
        results = search_google(query, num_results=20, category="poetry")
    elif category == "podcasts":
        results = search_google(query, num_results=20, category="podcasts")
    else:
        results = search_google(query, num_results=10, category="general")
    # Deduplicate results by title + source_url
    seen = set()
    unique_results = []
    for item in results:
        key = item.get("title", "") + item.get("source_url", "")
        if key not in seen:
            unique_results.append(item)
            seen.add(key)
    return unique_results[:100]

def save_user_profile(profile: dict, profile_path="art_recommender/user_profiles.json") -> bool:
    """
    Save user profile with updated timestamp
    """
    try:
        # Update the timestamp
        profile["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Ensure all required fields exist
        required_fields = ["past_favorite_work", "taste_genre", "current_obsession", "state_of_mind", "future_aspirations"]
        for field in required_fields:
            if field not in profile:
                profile[field] = "" if field != "past_favorite_work" and field != "current_obsession" else []
        
        # Ensure new fields exist
        if "uuid" not in profile:
            profile["uuid"] = ""
        if "complete" not in profile:
            profile["complete"] = False
        if "created_at" not in profile:
            profile["created_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Load existing data to preserve the UUID-keyed structure
        try:
            with open(profile_path, "r") as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {}
        
        # If existing_data is a dict with UUID keys, update the specific profile
        if isinstance(existing_data, dict) and len(existing_data) > 0:
            # Find the profile to update (use the first one if UUID not specified)
            profile_uuid = profile.get("uuid", "")
            if profile_uuid and profile_uuid in existing_data:
                # Map back to original field names for saving
                original_profile = existing_data[profile_uuid].copy()
                original_profile.update(profile)
                # Map expected field names back to original field names
                if "taste_genre" in profile and "favorite_taste_genre_description" not in profile:
                    original_profile["favorite_taste_genre_description"] = profile["taste_genre"]
                if "state_of_mind" in profile and "current_state_of_mind" not in profile:
                    original_profile["current_state_of_mind"] = profile["state_of_mind"]
                existing_data[profile_uuid] = original_profile
            else:
                # Update the first profile
                first_uuid = list(existing_data.keys())[0]
                original_profile = existing_data[first_uuid].copy()
                original_profile.update(profile)
                # Map expected field names back to original field names
                if "taste_genre" in profile and "favorite_taste_genre_description" not in profile:
                    original_profile["favorite_taste_genre_description"] = profile["taste_genre"]
                if "state_of_mind" in profile and "current_state_of_mind" not in profile:
                    original_profile["current_state_of_mind"] = profile["state_of_mind"]
                existing_data[first_uuid] = original_profile
                profile["uuid"] = first_uuid
            data_to_save = existing_data
        else:
            # Fallback to direct profile format
            data_to_save = profile
        
        # Save to file
        with open(profile_path, "w") as f:
            json.dump(data_to_save, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving user profile: {e}")
        return False 