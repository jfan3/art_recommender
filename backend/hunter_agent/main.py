# main.py
# 1. Load user profile and generate user embedding
# 2. Retrieve candidates from each domain and batch-generate embeddings
# 3. Main loop: recommend 5 items at a time, collect feedback, update user embedding, repeat
# 4. Stop when all candidates are seen or user quits, then output final personalized recommendations

from embedding import generate_user_embedding
from art_embedding import batch_generate_embeddings
from retriever import retrieve_top_candidates, load_user_profile, save_user_profile
from reranker import update_user_embedding
from formatter import format_for_user
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
from backend.db.supabase_client import upsert_item, upsert_user_item, update_user_item_status

# Step 1: Load user profile and generate user embedding
# Updated path to read from user_profiles.json in art_recommender folder
user_uuid = "your_test_uuid_here"  # Replace with actual uuid or pass as argument
user_profile = load_user_profile(user_uuid)
print(f"--- Loaded user profile (UUID: {user_profile.get('uuid', 'N/A')}) ---")
print(f"--- Profile completion status: {'Complete' if user_profile.get('complete', False) else 'Incomplete'} ---")

user_embedding = generate_user_embedding(user_uuid)
print("--- Initial user profile embedding generated. ---")

# Step 2: Retrieve an initial pool of candidates from each domain
print("--- Retrieving initial candidates from various domains... ---")
movie_candidates = retrieve_top_candidates("movies", user_embedding, user_profile)
book_candidates = retrieve_top_candidates("books", user_embedding, user_profile)
music_candidates = retrieve_top_candidates("music", user_embedding, user_profile)
art_candidates = retrieve_top_candidates("art", user_embedding, user_profile)
poetry_candidates = retrieve_top_candidates("poetry", user_embedding, user_profile)
podcast_candidates = retrieve_top_candidates("podcasts", user_embedding, user_profile)
musical_candidates = retrieve_top_candidates("musicals", user_embedding, user_profile)

# Step 3: Merge and enrich the pool with embeddings
# 拼接所有候选项，批量生成 embedding（包含 title/description/creator/category/release_date/metadata 等）
top_candidates = movie_candidates + book_candidates + music_candidates + art_candidates + poetry_candidates + podcast_candidates + musical_candidates
top_candidates = batch_generate_embeddings(top_candidates)
print(f"--- Pool of {len(top_candidates)} candidates ready for interaction. ---")

# --- Supabase: Log all candidates as items and user_item (status='candidate') ---
for candidate in top_candidates:
    item_data = {
        "item_id": candidate.get("source_url", ""),
        "item_name": candidate.get("title", ""),
        "description": candidate.get("description", ""),
        "source_url": candidate.get("source_url", ""),
        "image_url": candidate.get("image_url", ""),
        "category": candidate.get("category", ""),
        "creator": candidate.get("creator", ""),
        "release_date": candidate.get("release_date", ""),
        "metadata": candidate.get("metadata", {})
    }
    upsert_item(item_data)
    user_item_data = {
        "uuid": user_profile["uuid"],
        "item_id": item_data["item_id"],
        "status": "candidate"
    }
    upsert_user_item(user_item_data)

# Step 4: 主推荐-反馈-更新循环
current_embedding = user_embedding
seen_urls = set()
running = True
feedback_count = 0

# For sample generation, we'll simulate some feedback automatically
simulate_feedback = True  # Set to True for automatic sample generation

while running:
    # 1. 用当前 user embedding 对剩余候选项计算相似度，排序
    candidates_to_rank = [c for c in top_candidates if c.get('source_url') not in seen_urls and 'embedding' in c]
    if not candidates_to_rank:
        print("\n--- You've seen all available recommendations. ---")
        break
    candidate_embeddings = [c['embedding'] for c in candidates_to_rank]
    similarities = cosine_similarity([current_embedding], candidate_embeddings)[0]
    for i, c in enumerate(candidates_to_rank):
        c['score'] = similarities[i]
    sorted_candidates = sorted(candidates_to_rank, key=lambda x: x.get('score', 0), reverse=True)

    # 2. 取前5个未展示过的推荐项
    batch = sorted_candidates[:5]
    if not batch:
        break

    # 3. 展示5个推荐项，收集用户反馈（r/l/q）
    batch_feedback = []
    print("\n===== New Recommendation Batch =====")
    for idx, candidate in enumerate(batch, 1):
        print(f"\n[{idx}/5] Title: {candidate.get('title')}")
        print(f"Description: {candidate.get('description', 'No description available.')}")
        print(f"Creator: {candidate.get('creator', '')}")
        print(f"Category: {candidate.get('category', '')}")
        print(f"Release Date: {candidate.get('release_date', '')}")
        print(f"Source URL: {candidate.get('source_url', '')}")
        
        if simulate_feedback:
            # Simulate feedback for sample generation
            # Give positive feedback to first 2 items, negative to next 2, positive to last 1
            if idx <= 2:
                feedback = 'r'
                print("Swipe right (r) - [SIMULATED]")
            elif idx <= 4:
                feedback = 'l'
                print("Swipe left (l) - [SIMULATED]")
            else:
                feedback = 'r'
                print("Swipe right (r) - [SIMULATED]")
        else:
            feedback = ""
            while feedback not in ['r', 'l', 'q']:
                feedback = input("Swipe right (r), left (l), or (q)uit: ").lower()
        
        # --- Supabase: Update user_item status on swipe ---
        if feedback == 'r':
            update_user_item_status(user_profile["uuid"], candidate.get("source_url", ""), "swipe_right")
        elif feedback == 'l':
            update_user_item_status(user_profile["uuid"], candidate.get("source_url", ""), "swipe_left")
        if feedback == 'q':
            running = False
            break
        score = 1 if feedback == 'r' else 0
        batch_feedback.append(score)
        seen_urls.add(candidate.get('source_url'))

    if not running or not batch_feedback:
        break

    # 4. 用这5个反馈更新 user embedding，提升个性化
    batch_embeddings = [c['embedding'] for c in batch[:len(batch_feedback)]]
    current_embedding = update_user_embedding(current_embedding, batch_feedback, batch_embeddings)
    
    # 5. 更新用户配置文件
    feedback_count += len(batch_feedback)
    user_profile["complete"] = feedback_count >= 10  # Mark as complete after 10 feedbacks
    save_user_profile(user_profile, user_uuid)
    
    print("--- Profile updated! Your next recommendations will be more tailored. ---")
    print(f"--- Feedback count: {feedback_count}/10 (Profile {'Complete' if user_profile['complete'] else 'Incomplete'}) ---")
    
    # For sample generation, stop after 2 batches (10 feedbacks)
    if simulate_feedback and feedback_count >= 10:
        print("--- Sample generation complete. Stopping after 10 feedbacks. ---")
        break

# Step 5: 输出最终 personalized 推荐结果
print("\n=================================================")
print("--- Interaction ended. Here is your final personalized journey. ---")
final_output = format_for_user([c for c in top_candidates if c.get('source_url') in seen_urls])
print(json.dumps(final_output, indent=2))

# Save the final output to plan_agent/ranked_candidates_sample.json
output_path = "../plan_agent/ranked_candidates_sample.json"
try:
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    print(f"--- Final recommendations saved to {output_path} ---")
except Exception as e:
    print(f"--- Error saving to {output_path}: {e} ---")


# Tool Suggestions & APIs Used:
# - SerpAPI or Google Custom Search API: for long-tail web content
# - IMDb API / TMDB API: for movie metadata
# - Letterboxd Scraper: for niche/independent films
# - Goodreads API / OpenLibrary API: for book info
# - Spotify API / Last.fm API: for music metadata & similarity
# - Apple Music API: as alternative
# - Broadway World / Musical DB APIs: for musical theatre metadata
# - Optional: Bing Search API for extended coverage