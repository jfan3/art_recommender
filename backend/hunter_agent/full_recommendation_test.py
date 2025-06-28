#!/usr/bin/env python3
"""
Full recommendation test using user_profiles.json
"""

import sys
import os
import json
from typing import List, Dict

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever import retrieve_top_candidates, load_user_profile
from embedding import generate_user_embedding
from art_embedding import batch_generate_embeddings

def test_full_recommendation_pipeline():
    """Test the complete recommendation pipeline with user_profiles.json"""
    
    print("=== Full Recommendation Pipeline Test ===\n")
    
    # Step 1: Load user profile
    print("1. Loading user profile...")
    try:
        user_uuid = "your_test_uuid_here"  # Replace with actual uuid or pass as argument
        user_profile = load_user_profile(user_uuid)
        print(f"   ✅ Profile loaded for UUID: {user_profile.get('uuid', 'N/A')}")
        print(f"   📝 Taste: {user_profile.get('taste_genre', 'N/A')}")
        print(f"   ❤️  Favorites: {user_profile.get('past_favorite_work', [])}")
        print(f"   🎯 Current obsession: {user_profile.get('current_obsession', [])}")
        print(f"   😊 State of mind: {user_profile.get('state_of_mind', 'N/A')}")
        print(f"   🚀 Future aspirations: {user_profile.get('future_aspirations', 'N/A')}")
        print()
    except Exception as e:
        print(f"   ❌ Error loading profile: {e}")
        return
    
    # Step 2: Generate user embedding
    print("2. Generating user embedding...")
    try:
        user_embedding = generate_user_embedding(user_uuid)
        print(f"   ✅ User embedding generated (length: {len(user_embedding)})")
        print()
    except Exception as e:
        print(f"   ❌ Error generating embedding: {e}")
        return
    
    # Step 3: Retrieve candidates from all categories
    print("3. Retrieving candidates from all categories...")
    categories = ["movies", "books", "music", "art", "poetry", "musicals", "podcasts"]
    all_candidates = []
    
    for category in categories:
        print(f"   🔍 Searching {category}...")
        try:
            candidates = retrieve_top_candidates(category, user_embedding, user_profile)
            print(f"      ✅ Found {len(candidates)} {category} candidates")
            
            # Show top 2 results for each category
            for i, candidate in enumerate(candidates[:2], 1):
                domain = candidate.get('metadata', {}).get('domain', 'unknown')
                quality = candidate.get('metadata', {}).get('quality_score', 'unknown')
                print(f"         {i}. {candidate['title'][:60]}... ({domain}, {quality})")
            
            all_candidates.extend(candidates)
            print()
        except Exception as e:
            print(f"      ❌ Error retrieving {category}: {e}")
    
    print(f"   📊 Total candidates collected: {len(all_candidates)}")
    print()
    
    # Step 4: Generate embeddings for candidates
    print("4. Generating embeddings for candidates...")
    try:
        candidates_with_embeddings = batch_generate_embeddings(all_candidates)
        print(f"   ✅ Generated embeddings for {len(candidates_with_embeddings)} candidates")
        print()
    except Exception as e:
        print(f"   ❌ Error generating candidate embeddings: {e}")
        return
    
    # Step 5: Show final recommendations by category
    print("5. Final Recommendations by Category:")
    print("=" * 80)
    
    for category in categories:
        category_candidates = [c for c in candidates_with_embeddings if c.get('category') == category]
        if category_candidates:
            print(f"\n🎬 {category.upper()} RECOMMENDATIONS ({len(category_candidates)} items):")
            print("-" * 60)
            
            for i, candidate in enumerate(category_candidates[:3], 1):
                domain = candidate.get('metadata', {}).get('domain', 'unknown')
                quality = candidate.get('metadata', {}).get('quality_score', 'unknown')
                
                print(f"{i}. {candidate['title']}")
                print(f"   📝 {candidate['description'][:100]}...")
                print(f"   🎨 Creator: {candidate.get('creator', 'N/A')}")
                print(f"   📅 Release: {candidate.get('release_date', 'N/A')}")
                print(f"   🌐 Source: {domain} (Quality: {quality})")
                print(f"   🔗 URL: {candidate['source_url']}")
                print()
    
    # Step 6: Quality analysis
    print("6. Quality Analysis:")
    print("=" * 80)
    
    quality_stats = {}
    domain_stats = {}
    
    for candidate in candidates_with_embeddings:
        category = candidate.get('category', 'unknown')
        quality = candidate.get('metadata', {}).get('quality_score', 'unknown')
        domain = candidate.get('metadata', {}).get('domain', 'unknown')
        
        if category not in quality_stats:
            quality_stats[category] = {'high': 0, 'medium': 0, 'unknown': 0}
        quality_stats[category][quality] += 1
        
        if domain not in domain_stats:
            domain_stats[domain] = 0
        domain_stats[domain] += 1
    
    print("\n📊 Quality Distribution by Category:")
    for category, stats in quality_stats.items():
        total = sum(stats.values())
        if total > 0:
            high_pct = (stats['high'] / total) * 100
            print(f"   {category}: {stats['high']}/{total} high quality ({high_pct:.1f}%)")
    
    print(f"\n🏆 Top 5 Domains:")
    sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)
    for domain, count in sorted_domains[:5]:
        print(f"   {domain}: {count} results")
    
    print(f"\n✅ Test completed successfully!")
    print(f"📈 Total high-quality recommendations: {len(candidates_with_embeddings)}")

def main():
    """Run the full recommendation test"""
    print("Testing Complete Recommendation Pipeline with user_profiles.json\n")
    print("=" * 80)
    
    test_full_recommendation_pipeline()

if __name__ == "__main__":
    main() 