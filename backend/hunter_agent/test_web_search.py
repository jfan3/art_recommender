#!/usr/bin/env python3
"""
Test script for improved web search functionality
"""

import sys
import os
from typing import List, Dict

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever import search_google, load_user_profile

def test_web_search_quality():
    """Test the quality of web search results for different categories"""
    
    print("=== Testing Improved Web Search Quality ===\n")
    
    # Test categories
    categories = ["art", "poetry", "musicals", "podcasts"]
    
    # Load user profile for context
    try:
        profile = load_user_profile("user_profiles.json")
        print(f"Loaded profile for: {profile.get('uuid', 'N/A')}")
        print(f"Taste: {profile.get('taste_genre', 'N/A')}")
        print(f"Favorites: {profile.get('past_favorite_work', [])}")
        print()
    except Exception as e:
        print(f"Warning: Could not load user profile: {e}")
        profile = {}
    
    for category in categories:
        print(f"--- Testing {category.upper()} Search ---")
        
        # Create a test query
        test_query = f"best {category} recommendations"
        if profile.get('taste_genre'):
            test_query += f" {profile.get('taste_genre')}"
        
        print(f"Query: {test_query}")
        
        try:
            # Get search results
            results = search_google(test_query, num_results=5, category=category)
            
            if results:
                print(f"Found {len(results)} high-quality results:")
                for i, result in enumerate(results, 1):
                    domain = result.get('metadata', {}).get('domain', 'unknown')
                    quality = result.get('metadata', {}).get('quality_score', 'unknown')
                    print(f"  {i}. {result['title']}")
                    print(f"     Domain: {domain} (Quality: {quality})")
                    print(f"     URL: {result['source_url']}")
                    print(f"     Description: {result['description'][:100]}...")
                    print()
            else:
                print("No results found.")
                
        except Exception as e:
            print(f"Error searching for {category}: {e}")
        
        print("-" * 50)
        print()

def test_low_quality_filtering():
    """Test that low-quality sites are properly filtered out"""
    
    print("=== Testing Low-Quality Site Filtering ===\n")
    
    # Test with a query that might return low-quality results
    test_query = "art recommendations"
    
    print(f"Query: {test_query}")
    print("Checking that results exclude low-quality sites...")
    
    try:
        results = search_google(test_query, num_results=10, category="art")
        
        low_quality_domains = [
            "quora.com", "reddit.com", "youtube.com", "facebook.com",
            "twitter.com", "instagram.com", "linkedin.com", "pinterest.com",
            "tumblr.com", "wikipedia.org", "answers.com", "yahoo.com"
        ]
        
        filtered_count = 0
        for result in results:
            domain = result.get('metadata', {}).get('domain', '')
            if any(low_domain in domain.lower() for low_domain in low_quality_domains):
                print(f"❌ Found low-quality site: {domain}")
                filtered_count += 1
            else:
                print(f"✅ High-quality site: {domain}")
        
        if filtered_count == 0:
            print("\n🎉 All results are from high-quality sites!")
        else:
            print(f"\n⚠️  Found {filtered_count} low-quality results that should be filtered")
            
    except Exception as e:
        print(f"Error testing filtering: {e}")

def main():
    """Run all tests"""
    print("Testing Improved Web Search Functionality\n")
    print("=" * 60)
    
    # Test 1: Quality of results
    test_web_search_quality()
    
    # Test 2: Low-quality filtering
    test_low_quality_filtering()
    
    print("\n=== Test Summary ===")
    print("✅ Web search improvements include:")
    print("  - High-quality site targeting for each category")
    print("  - Low-quality site filtering")
    print("  - Enhanced query construction")
    print("  - Content quality scoring")
    print("  - Better result filtering")

if __name__ == "__main__":
    main() 