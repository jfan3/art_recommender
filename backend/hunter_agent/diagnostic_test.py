#!/usr/bin/env python3
"""
Diagnostic test to check why some categories return 0 results
"""

import sys
import os
from typing import List, Dict

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever import (
    search_tmdb, search_openlibrary, search_google, search_spotify,
    build_query, load_user_profile
)

def test_individual_apis():
    """Test each API individually to see which ones work"""
    
    print("=== Individual API Diagnostic Test ===\n")
    
    # Load user profile
    try:
        profile = load_user_profile("../../user_profiles.json")
        print(f"✅ Profile loaded: {profile.get('taste_genre', 'N/A')}")
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        return
    
    # Test each API with a simple query
    test_queries = {
        "movies": "horror romance donnie darko",
        "books": "horror romance donnie darko",
        "art": "contemporary art horror romance",
        "poetry": "contemporary poetry horror romance",
        "musicals": "musical theatre horror romance",
        "podcasts": "podcast horror romance"
    }
    
    for category, query in test_queries.items():
        print(f"\n🔍 Testing {category.upper()} API...")
        print(f"   Query: {query}")
        
        try:
            if category == "movies":
                results = search_tmdb(query, num_results=5)
            elif category == "books":
                results = search_openlibrary(query, num_results=5)
            elif category in ["art", "poetry", "musicals", "podcasts"]:
                results = search_google(query, num_results=5, category=category)
            else:
                results = []
            
            if results:
                print(f"   ✅ Found {len(results)} results")
                for i, result in enumerate(results[:2], 1):
                    print(f"      {i}. {result['title'][:50]}...")
            else:
                print(f"   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_environment_variables():
    """Check if required environment variables are set"""
    
    print("\n=== Environment Variables Check ===\n")
    
    required_vars = [
        "SERPAPI_API_KEY",
        "TMDB_API_KEY", 
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 8)}...")
        else:
            print(f"❌ {var}: NOT SET")

def test_query_building():
    """Test query building with user profile"""
    
    print("\n=== Query Building Test ===\n")
    
    try:
        profile = load_user_profile("../../user_profiles.json")
        
        categories = ["movies", "books", "music", "art", "poetry", "musicals", "podcasts"]
        
        for category in categories:
            query = build_query(category, profile)
            print(f"{category}: {query}")
            
    except Exception as e:
        print(f"❌ Error testing query building: {e}")

def main():
    """Run all diagnostic tests"""
    print("Diagnostic Test for Recommendation System\n")
    print("=" * 60)
    
    test_environment_variables()
    test_query_building()
    test_individual_apis()
    
    print("\n=== Diagnostic Summary ===")
    print("This test will help identify why some categories return 0 results.")

if __name__ == "__main__":
    main() 