#!/usr/bin/env python3
"""
Quick test to validate search function data structures
"""

from retriever import search_openlibrary, search_google, search_tmdb, search_spotify

def validate_result(result, expected_type):
    """Quick validation of result structure"""
    required_fields = ["title", "description", "source_url", "image_url", "type", "category", "creator", "release_date", "metadata"]
    
    # Check all required fields exist
    for field in required_fields:
        if field not in result:
            print(f"  ✗ Missing field: {field}")
            return False
    
    # Check type is correct
    if result["type"] != expected_type:
        print(f"  ✗ Wrong type: expected {expected_type}, got {result['type']}")
        return False
    
    # Check metadata is dict
    if not isinstance(result["metadata"], dict):
        print(f"  ✗ Metadata not a dict: {type(result['metadata'])}")
        return False
    
    return True

def main():
    print("Quick validation of search function data structures")
    print("="*50)
    
    # Test each search function
    functions = [
        ("OpenLibrary", search_openlibrary, "book", "science fiction"),
        ("Google", search_google, "web", "art recommendations"),
        ("TMDB", search_tmdb, "movie", "sci-fi movies"),
        ("Spotify", search_spotify, "music", "indie rock")
    ]
    
    all_passed = True
    
    for name, func, expected_type, query in functions:
        print(f"\nTesting {name}...")
        try:
            results = func(query, 1)
            if results:
                if validate_result(results[0], expected_type):
                    print(f"  ✓ {name} structure valid")
                    print(f"  ✓ Sample result: {results[0]['title']}")
                else:
                    print(f"  ✗ {name} structure invalid")
                    all_passed = False
            else:
                print(f"  ⚠️  {name} returned no results")
        except Exception as e:
            print(f"  ✗ {name} error: {e}")
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All search functions validated successfully!")
        print("✅ Data structures are consistent and correct")
    else:
        print("⚠️  Some validation issues found")
    
    return all_passed

if __name__ == "__main__":
    main() 