#!/usr/bin/env python3
"""
Test script for all search functions in retriever.py
"""

import sys
import os
import json
from typing import List, Dict

# Add the current directory to the path so we can import retriever
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever import (
    search_openlibrary,
    search_google,
    search_tmdb,
    search_spotify,
    retrieve_top_candidates,
    build_query,
    load_user_profile,
    get_spotify_access_token
)

def test_search_openlibrary():
    """Test OpenLibrary book search"""
    print("\n" + "="*50)
    print("Testing search_openlibrary()")
    print("="*50)
    
    query = "science fiction books"
    print(f"Query: {query}")
    
    try:
        results = search_openlibrary(query, num_results=5)
        print(f"Found {len(results)} results")
        
        if results:
            print("\nFirst result:")
            first_result = results[0]
            for key, value in first_result.items():
                if key == "metadata":
                    print(f"  {key}: {json.dumps(value, indent=4)}")
                else:
                    print(f"  {key}: {value}")
        
        return len(results) > 0
    except Exception as e:
        print(f"Error testing search_openlibrary: {e}")
        return False

def test_search_google():
    """Test Google search via SerpAPI"""
    print("\n" + "="*50)
    print("Testing search_google()")
    print("="*50)
    
    query = "art recommendations"
    print(f"Query: {query}")
    
    try:
        results = search_google(query, num_results=5)
        print(f"Found {len(results)} results")
        
        if results:
            print("\nFirst result:")
            first_result = results[0]
            for key, value in first_result.items():
                if key == "metadata":
                    print(f"  {key}: {json.dumps(value, indent=4)}")
                else:
                    print(f"  {key}: {value}")
        
        return len(results) > 0
    except Exception as e:
        print(f"Error testing search_google: {e}")
        return False

def test_search_tmdb():
    """Test TMDB movie search"""
    print("\n" + "="*50)
    print("Testing search_tmdb()")
    print("="*50)
    
    query = "sci-fi movies"
    print(f"Query: {query}")
    
    try:
        results = search_tmdb(query, num_results=5)
        print(f"Found {len(results)} results")
        
        if results:
            print("\nFirst result:")
            first_result = results[0]
            for key, value in first_result.items():
                if key == "metadata":
                    print(f"  {key}: {json.dumps(value, indent=4)}")
                else:
                    print(f"  {key}: {value}")
        
        return len(results) > 0
    except Exception as e:
        print(f"Error testing search_tmdb: {e}")
        return False

def test_search_spotify():
    """Test Spotify music search"""
    print("\n" + "="*50)
    print("Testing search_spotify()")
    print("="*50)
    
    query = "indie rock"
    print(f"Query: {query}")
    
    try:
        # First test token generation
        print("Testing Spotify token generation...")
        token = get_spotify_access_token()
        if token:
            print("✓ Spotify token generated successfully")
        else:
            print("✗ Failed to generate Spotify token")
            return False
        
        results = search_spotify(query, num_results=5)
        print(f"Found {len(results)} results")
        
        if results:
            print("\nFirst result:")
            first_result = results[0]
            for key, value in first_result.items():
                if key == "metadata":
                    print(f"  {key}: {json.dumps(value, indent=4)}")
                else:
                    print(f"  {key}: {value}")
        
        return len(results) > 0
    except Exception as e:
        print(f"Error testing search_spotify: {e}")
        return False

def test_build_query():
    """Test query building function"""
    print("\n" + "="*50)
    print("Testing build_query()")
    print("="*50)
    
    # Create a sample user profile
    profile = {
        "taste_genre": "sci-fi and fantasy",
        "past_favorite_work": ["Dune", "The Matrix"],
        "current_obsession": ["cyberpunk aesthetics"],
        "state_of_mind": "feeling adventurous",
        "complete": True
    }
    
    categories = ["movies", "books", "music", "musicals", "art"]
    
    for category in categories:
        query = build_query(category, profile)
        print(f"{category}: {query}")
    
    return True

def test_retrieve_top_candidates():
    """Test the main retrieve_top_candidates function"""
    print("\n" + "="*50)
    print("Testing retrieve_top_candidates()")
    print("="*50)
    
    # Create a sample user profile
    profile = {
        "taste_genre": "sci-fi and fantasy",
        "past_favorite_work": ["Dune", "The Matrix"],
        "current_obsession": ["cyberpunk aesthetics"],
        "state_of_mind": "feeling adventurous",
        "complete": True
    }
    
    # Create a dummy embedding (not actually used in the function)
    user_embedding = [0.1] * 384  # Assuming 384-dimensional embedding
    
    categories = ["books", "movies", "music", "musicals"]
    
    for category in categories:
        print(f"\nTesting category: {category}")
        try:
            results = retrieve_top_candidates(category, user_embedding, profile)
            print(f"Found {len(results)} results for {category}")
            
            if results:
                print(f"First result title: {results[0].get('title', 'N/A')}")
                print(f"First result type: {results[0].get('type', 'N/A')}")
        
        except Exception as e:
            print(f"Error testing {category}: {e}")
    
    return True

def test_load_user_profile():
    """Test user profile loading"""
    print("\n" + "="*50)
    print("Testing load_user_profile()")
    print("="*50)
    
    try:
        # Use the correct path to user_profiles.json in the root directory
        profile = load_user_profile("../../user_profiles.json")
        print("Profile loaded successfully")
        print(f"Profile keys: {list(profile.keys())}")
        
        # Check required fields
        required_fields = ["past_favorite_work", "taste_genre", "current_obsession", "state_of_mind", "future_aspirations"]
        for field in required_fields:
            if field in profile:
                print(f"✓ {field}: {profile[field]}")
            else:
                print(f"✗ Missing {field}")
        
        return True
    except Exception as e:
        print(f"Error loading user profile: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting comprehensive test of retriever.py functions")
    print("="*60)
    
    test_results = {}
    
    # Test individual search functions
    test_results["openlibrary"] = test_search_openlibrary()
    test_results["google"] = test_search_google()
    test_results["tmdb"] = test_search_tmdb()
    test_results["spotify"] = test_search_spotify()
    
    # Test utility functions
    test_results["build_query"] = test_build_query()
    test_results["load_profile"] = test_load_user_profile()
    test_results["retrieve_candidates"] = test_retrieve_top_candidates()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 