#!/usr/bin/env python3
"""
Show actual recommendations from retriever for current user profile
"""

import sys
import os
import json
from typing import List, Dict

# Add the current directory to the path so we can import retriever
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever import (
    retrieve_top_candidates,
    load_user_profile,
    build_query
)

def display_recommendations(category: str, results: List[Dict], max_display: int = 5):
    """Display recommendations in a nice format"""
    print(f"\n{'='*60}")
    print(f"RECOMMENDATIONS FOR: {category.upper()}")
    print(f"{'='*60}")
    
    if not results:
        print("❌ No recommendations found")
        return
    
    print(f"Found {len(results)} total recommendations")
    print(f"Showing top {min(max_display, len(results))} results:\n")
    
    for i, result in enumerate(results[:max_display], 1):
        print(f"{i}. {result.get('title', 'No title')}")
        print(f"   Type: {result.get('type', 'Unknown')}")
        
        if result.get('creator'):
            print(f"   Creator: {result['creator']}")
        
        if result.get('description'):
            desc = result['description'][:100] + "..." if len(result['description']) > 100 else result['description']
            print(f"   Description: {desc}")
        
        if result.get('release_date'):
            print(f"   Release Date: {result['release_date']}")
        
        if result.get('metadata', {}).get('rating'):
            print(f"   Rating: {result['metadata']['rating']}")
        
        if result.get('source_url'):
            print(f"   Source: {result['source_url']}")
        
        print()

def main():
    """Show recommendations for current user profile"""
    print("🎯 SHOWING RECOMMENDATIONS FOR CURRENT USER PROFILE")
    print("="*80)
    
    # Load the current user profile
    try:
        profile = load_user_profile("../../user_profiles.json")
        print("✅ User profile loaded successfully")
        print(f"   Taste: {profile.get('taste_genre', 'N/A')}")
        print(f"   Past favorites: {profile.get('past_favorite_work', [])}")
        print(f"   Current obsessions: {profile.get('current_obsession', [])}")
        print(f"   State of mind: {profile.get('state_of_mind', 'N/A')}")
        print(f"   Profile complete: {profile.get('complete', False)}")
    except Exception as e:
        print(f"❌ Error loading user profile: {e}")
        return
    
    # Create a dummy embedding (not actually used in the function)
    user_embedding = [0.1] * 384
    
    # Test categories
    categories = ["books", "movies", "music", "musicals", "art", "poetry"]
    
    print(f"\n🔍 Generating recommendations for {len(categories)} categories...")
    
    for category in categories:
        print(f"\n📋 Processing {category}...")
        
        # Show the query being built
        query = build_query(category, profile)
        print(f"   Query: {query}")
        
        try:
            # Get recommendations
            results = retrieve_top_candidates(category, user_embedding, profile)
            
            # Display results
            display_recommendations(category, results, max_display=5)
            
        except Exception as e:
            print(f"❌ Error getting {category} recommendations: {e}")
    
    print(f"\n{'='*80}")
    print("🎉 Recommendation generation complete!")
    print("💡 The retriever uses your profile to find personalized content")
    print("   based on your taste, past favorites, and current interests.")

if __name__ == "__main__":
    main() 