#!/usr/bin/env python3
"""
Test script for the complete embedding-based recommendation workflow.
This script tests the integration of user embeddings, item embeddings, and reranking.
"""

import sys
import os
from pathlib import Path

# Add parent directories to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.supabase_client import (
    upsert_user_profile, get_user_profile, upsert_user_item, 
    get_user_embedding, get_item_embedding
)
from backend.hunter_agent.embedding import generate_user_embedding
from backend.hunter_agent.art_embedding import batch_generate_embeddings, generate_item_id
from backend.hunter_agent.reranker import update_user_embedding_from_swipes, get_personalized_candidates
import uuid
import json

def create_test_user_profile():
    """Create a test user profile for testing."""
    
    test_uuid = f"test-embedding-{uuid.uuid4().hex[:8]}"
    
    profile = {
        "uuid": test_uuid,
        "past_favorite_work": ["The Great Gatsby", "Mona Lisa", "Bohemian Rhapsody"],
        "taste_genre": "Contemporary art and classic literature",
        "current_obsession": ["Abstract expressionism", "Jazz music"],
        "state_of_mind": "Curious and contemplative",
        "future_aspirations": "To understand the intersection of art and technology",
        "complete": True
    }
    
    print(f"Creating test user profile: {test_uuid}")
    result = upsert_user_profile(profile)
    print(f"✅ Profile created: {result}")
    
    return test_uuid

def test_user_embedding_generation(user_uuid):
    """Test user embedding generation and storage."""
    
    print(f"\n🧠 Testing user embedding generation for {user_uuid}")
    
    # Generate and store embedding
    embedding = generate_user_embedding(user_uuid, store_in_db=True)
    
    print(f"✅ User embedding generated: {len(embedding)} dimensions")
    
    # Verify storage
    stored_embedding = get_user_embedding(user_uuid)
    
    if stored_embedding:
        print(f"✅ Embedding stored in database (version {stored_embedding['version']})")
        print(f"   First 5 values: {stored_embedding['embedding'][:5]}")
        return True
    else:
        print("❌ Embedding not found in database")
        return False

def test_item_embedding_generation():
    """Test item embedding generation and storage."""
    
    print(f"\n🎨 Testing item embedding generation")
    
    # Create test items
    test_items = [
        {
            "title": "Starry Night",
            "description": "A swirling night sky painting by Vincent van Gogh",
            "creator": "Vincent van Gogh",
            "category": "Post-Impressionist painting",
            "source_url": "https://example.com/starry-night",
            "metadata": {"medium": "Oil on canvas", "year": "1889"}
        },
        {
            "title": "Abbey Road",
            "description": "Iconic album by The Beatles featuring innovative recording techniques",
            "creator": "The Beatles", 
            "category": "Rock album",
            "source_url": "https://example.com/abbey-road",
            "metadata": {"genre": "Rock", "year": "1969"}
        }
    ]
    
    # Generate embeddings
    enriched_items = batch_generate_embeddings(test_items, store_in_db=True)
    
    print(f"✅ Generated embeddings for {len(enriched_items)} items")
    
    # Verify storage
    for item in enriched_items:
        item_id = item.get("item_id")
        stored_embedding = get_item_embedding(item_id)
        
        if stored_embedding:
            print(f"✅ Item {item_id} embedding stored (dimensions: {len(stored_embedding['embedding'])})")
        else:
            print(f"❌ Item {item_id} embedding not found")
            return False
    
    return enriched_items

def test_swipe_simulation(user_uuid, test_items):
    """Simulate user swipes to test the reranking workflow."""
    
    print(f"\n👆 Testing swipe simulation and reranking")
    
    # Create user_item entries for swiping
    for i, item in enumerate(test_items):
        item_id = item.get("item_id")
        
        # Simulate swipes (like first item, dislike second)
        status = "swipe_right" if i == 0 else "swipe_left"
        
        user_item_data = {
            "uuid": user_uuid,
            "item_id": item_id,
            "status": status
        }
        
        result = upsert_user_item(user_item_data)
        print(f"✅ Simulated {status} for item {item_id}")
    
    # Test embedding update from swipes
    try:
        updated_embedding = update_user_embedding_from_swipes(user_uuid)
        print(f"✅ User embedding updated based on swipes")
        print(f"   Updated embedding first 5 values: {updated_embedding[:5]}")
        return True
    except Exception as e:
        print(f"❌ Error updating embedding from swipes: {e}")
        return False

def test_personalized_recommendations(user_uuid):
    """Test personalized recommendation generation."""
    
    print(f"\n🎯 Testing personalized recommendations")
    
    try:
        recommendations = get_personalized_candidates(user_uuid, limit=5)
        
        if recommendations:
            print(f"✅ Generated {len(recommendations)} personalized recommendations")
            for i, rec in enumerate(recommendations):
                score = rec.get("score", 0)
                title = rec.get("item_name", rec.get("title", "Unknown"))
                print(f"   {i+1}. {title} (similarity: {score:.4f})")
            return True
        else:
            print("⚠️  No personalized recommendations generated")
            return False
            
    except Exception as e:
        print(f"❌ Error generating recommendations: {e}")
        return False

def cleanup_test_data(user_uuid):
    """Clean up test data (optional)."""
    
    print(f"\n🧹 Cleaning up test data...")
    print(f"Note: Test data with UUID {user_uuid} can be manually removed from Supabase if needed")

def run_full_test():
    """Run the complete embedding workflow test."""
    
    print("🚀 Starting Complete Embedding Workflow Test")
    print("=" * 50)
    
    # Step 1: Create test user
    user_uuid = create_test_user_profile()
    
    # Step 2: Test user embedding
    user_embedding_success = test_user_embedding_generation(user_uuid)
    
    # Step 3: Test item embedding
    test_items = test_item_embedding_generation()
    item_embedding_success = test_items is not False
    
    # Step 4: Test swipe simulation and reranking
    swipe_success = False
    if user_embedding_success and item_embedding_success:
        swipe_success = test_swipe_simulation(user_uuid, test_items)
    
    # Step 5: Test personalized recommendations
    recommendation_success = False
    if swipe_success:
        recommendation_success = test_personalized_recommendations(user_uuid)
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary")
    print("=" * 50)
    print(f"✅ User Profile Creation: {'PASS' if user_uuid else 'FAIL'}")
    print(f"✅ User Embedding: {'PASS' if user_embedding_success else 'FAIL'}")
    print(f"✅ Item Embedding: {'PASS' if item_embedding_success else 'FAIL'}")
    print(f"✅ Swipe & Reranking: {'PASS' if swipe_success else 'FAIL'}")
    print(f"✅ Personalized Recs: {'PASS' if recommendation_success else 'FAIL'}")
    
    overall_success = all([
        user_uuid, user_embedding_success, item_embedding_success, 
        swipe_success, recommendation_success
    ])
    
    if overall_success:
        print("\n🎉 All tests passed! Embedding workflow is working correctly.")
        print(f"\nTest user UUID: {user_uuid}")
        print("You can now test the full workflow in the frontend!")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        print("Make sure:")
        print("1. Supabase environment variables are set")
        print("2. Database tables are created (run setup_database.py)")
        print("3. OpenAI API key is configured")
    
    return overall_success

if __name__ == "__main__":
    # Check environment variables
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        print("❌ Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables")
        sys.exit(1)
        
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Please set OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    success = run_full_test()
    sys.exit(0 if success else 1)