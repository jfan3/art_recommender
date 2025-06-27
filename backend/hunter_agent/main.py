# main.py
# 1. Load user profile and generate user embedding
# 2. Retrieve candidates from each domain and batch-generate embeddings
# 3. Main loop: recommend 5 items at a time, collect feedback, update user embedding, repeat
# 4. Stop when all candidates are seen or user quits, then output final personalized recommendations

from .embedding import generate_user_embedding
from .art_embedding import batch_generate_embeddings
from .retriever import retrieve_top_candidates
from .reranker import update_user_embedding
from .formatter import format_for_user
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

# Step 1: Generate user embedding from JSON profile
# Updated path to read from user_profiles.json in art_recommender folder
user_profile_path = "art_recommender/user_profiles.json"
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
# 拼接所有候选项，批量生成 embedding（包含 title/description/creator/category/release_date/metadata 等）
top_candidates = movie_candidates + book_candidates + music_candidates + art_candidates + poetry_candidates + podcast_candidates + musical_candidates
top_candidates = batch_generate_embeddings(top_candidates)
print(f"--- Pool of {len(top_candidates)} candidates ready for interaction. ---")

# Step 4: 主推荐-反馈-更新循环
current_embedding = user_embedding
seen_urls = set()
running = True

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
        feedback = ""
        while feedback not in ['r', 'l', 'q']:
            feedback = input("Swipe right (r), left (l), or (q)uit: ").lower()
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
    print("--- Profile updated! Your next recommendations will be more tailored. ---")

# Step 5: 输出最终 personalized 推荐结果
print("\n=================================================")
print("--- Interaction ended. Here is your final personalized journey. ---")
final_output = format_for_user([c for c in top_candidates if c.get('source_url') in seen_urls])
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