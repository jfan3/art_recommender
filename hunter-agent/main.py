# main.py
from embedding import generate_user_embedding
from art_embedding import batch_generate_embeddings
from retriever import retrieve_top_candidates
from reranker import update_user_embedding
from formatter import format_for_user
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

# Step 1: Generate user embedding from JSON profile
user_profile_path = "hunter-agent/profiling_output_sample.json"
user_embedding = generate_user_embedding(user_profile_path)
print("--- Initial user profile embedding generated. ---")

# Step 2: Retrieve an initial pool of candidates from each domain
print("--- Retrieving initial candidates from various domains... ---")
movie_candidates = retrieve_top_candidates("movies", user_embedding)
book_candidates = retrieve_top_candidates("books", user_embedding)
music_candidates = retrieve_top_candidates("music", user_embedding)
art_candidates = retrieve_top_candidates("art", user_embedding)
poetry_candidates = retrieve_top_candidates("poetry", user_embedding)
podcast_candidates = retrieve_top_candidates("podcasts", user_embedding)
musical_candidates = retrieve_top_candidates("musicals", user_embedding)

# Step 3: Merge and enrich the pool with embeddings
top_candidates = movie_candidates + book_candidates + music_candidates + art_candidates + poetry_candidates + podcast_candidates + musical_candidates
top_candidates = batch_generate_embeddings(top_candidates, text_field="title")
print(f"--- Pool of {len(top_candidates)} candidates ready for interaction. ---")


# --- Main Interaction Loop ---
current_embedding = user_embedding
seen_urls = set()
feedback_batch = []
running = True

while running and len(seen_urls) < len(top_candidates):
    # Re-rank all candidates based on the current embedding
    candidate_embeddings = [c['embedding'] for c in top_candidates if 'embedding' in c]
    similarities = cosine_similarity([current_embedding], candidate_embeddings)[0]
    for i, c in enumerate(top_candidates):
        c['score'] = similarities[i]

    sorted_candidates = sorted(top_candidates, key=lambda x: x.get('score', 0), reverse=True)

    # Find the next best candidate that hasn't been seen
    next_candidate = None
    for candidate in sorted_candidates:
        if candidate.get('source_url') not in seen_urls:
            next_candidate = candidate
            break
    
    if not next_candidate:
        print("\n--- You've seen all available recommendations. ---")
        break

    # Step 4: Present candidate and get swipe feedback
    print("\n=================================================")
    print(f"Title: {next_candidate.get('title')}")
    print(f"Description: {next_candidate.get('description', 'No description available.')}")
    print(f"Image URL: {next_candidate.get('image_url', 'N/A')}")
    
    feedback_input = ""
    while feedback_input not in ['r', 'l', 'q']:
        feedback_input = input("Swipe right (r), left (l), or (q)uit: ").lower()

    if feedback_input == 'q':
        running = False
        continue

    # Record feedback
    feedback_score = 1 if feedback_input == 'r' else 0
    feedback_batch.append({"candidate": next_candidate, "feedback": feedback_score})
    seen_urls.add(next_candidate.get('source_url'))

    # Step 5: Update user embedding every 5 swipes
    if len(feedback_batch) == 5:
        print("\n--- 5 swipes recorded. Updating your profile... ---")
        
        batch_embeddings = [fb['candidate']['embedding'] for fb in feedback_batch]
        batch_scores = [fb['feedback'] for fb in feedback_batch]
        
        current_embedding = update_user_embedding(current_embedding, batch_scores, batch_embeddings)
        print("--- Profile updated! Your next recommendations will be more tailored. ---")
        
        feedback_batch = [] # Reset for the next batch

# --- End of Loop ---
print("\n=================================================")
print("--- Interaction ended. Here is your final personalized journey. ---")
final_output = format_for_user(sorted_candidates)
# We can use print(json.dumps(final_output, indent=2)) for better readability if needed
print(json.dumps(final_output, indent=2))

# Tool Suggestions & APIs Used:
# - SerpAPI or Google Custom Search API: for long-tail web content
# - IMDb API / TMDB API: for movie metadata
# - Letterboxd Scraper: for niche/independent films
# - Goodreads API / OpenLibrary API: for book info
# - Spotify API / Last.fm API: for music metadata & similarity
# - Apple Music API: as alternative
# - Broadway World / Musical DB APIs: for musical theatre metadata
# - Optional: Bing Search API for extended coverage