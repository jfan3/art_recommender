# Embedding-Based Recommendation Workflow

This document explains the enhanced recommendation system that uses user and item embeddings to provide personalized art recommendations based on user preferences.

## Overview

The system implements the following workflow based on the diagram provided:

```
用户 profile → embedding.py → 用户 embedding
     ↓
初步推荐 → 用户 swipe 5个 → reranker.py → 更新用户 embedding
     ↓                                    ↓
API 检索 top 100 → art_embedding.py → 候选项 embedding
     ↓                                    ↓
最终相似度排序 ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
     ↓
输出 personalized candidates
```

## Key Components

### 1. Database Schema

#### User Embeddings Table (`user_embedding`)
- `uuid`: User identifier (foreign key to user_profile)
- `embedding`: 1536-dimension vector representing user preferences
- `version`: Version number for tracking embedding updates
- `created_at`/`updated_at`: Timestamps

#### Item Embeddings Table (`item_embedding`)
- `item_id`: Item identifier (foreign key to item)
- `embedding`: 1536-dimension vector representing item content
- `created_at`/`updated_at`: Timestamps

### 2. Core Modules

#### `embedding.py`
- **Purpose**: Generate user embeddings from profile text
- **Key Function**: `generate_user_embedding(user_uuid, store_in_db=True)`
- **Features**:
  - Extracts meaningful text from user profile fields
  - Uses OpenAI `text-embedding-ada-002` model
  - Stores embeddings in database with versioning
  - Checks for existing embeddings to avoid regeneration

#### `art_embedding.py`
- **Purpose**: Generate item embeddings from content
- **Key Function**: `batch_generate_embeddings(candidates, store_in_db=True)`
- **Features**:
  - Combines title, description, creator, category, metadata
  - Uses OpenAI `text-embedding-3-small` model
  - Batch processing for efficiency
  - Persistent storage in database

#### `reranker.py`
- **Purpose**: Update user embeddings based on feedback and rerank candidates
- **Key Functions**:
  - `update_user_embedding_from_swipes(user_uuid)`: Updates user embedding based on swipe history
  - `get_personalized_candidates(user_uuid, limit=10)`: Gets ranked recommendations
- **Features**:
  - Reinforces liked items (+0.1 weight)
  - Discourages disliked items (-0.05 weight)
  - Normalizes updated embeddings
  - Version tracking for embedding evolution

### 3. API Integration

#### Enhanced Endpoints

##### `GET /api/candidates/{user_uuid}`
- **Behavior Change**: After 5+ right swipes, switches to personalized recommendations
- **Logic**:
  - 0-4 right swipes: Original random/similarity-based recommendations
  - 5+ right swipes: Embedding-based personalized recommendations via `get_personalized_candidates()`

##### `POST /api/swipe`
- **Enhanced Behavior**: Updates user embedding after every 5 total swipes
- **Logic**:
  - Records swipe in database
  - Counts total swipes (left + right)
  - Triggers `update_user_embedding_from_swipes()` every 5 swipes
  - Continues with training completion logic (30 right swipes)

##### `POST /api/generate_candidates/{user_uuid}`
- **Enhanced Behavior**: Stores both user and item embeddings
- **Logic**:
  - Generates and stores user embedding on profile completion
  - Retrieves candidates from all sources
  - Generates and stores item embeddings for all candidates

## Workflow Steps

### 1. Initial Setup (One-time)
```bash
# Create database tables
cd backend/db
python setup_database.py

# Test the workflow
cd ../hunter_agent
python test_embedding_workflow.py
```

### 2. User Onboarding
1. User completes profile via chat interface
2. Profile triggers `/api/generate_candidates/{user_uuid}`
3. System generates user embedding from profile text
4. System retrieves top 100 candidates from all sources
5. System generates item embeddings for all candidates
6. Both embeddings stored in database
7. User starts swiping with initial candidates

### 3. Learning Phase (First 5 Swipes)
1. User swipes on initial candidates
2. System records swipe preferences
3. After 5 total swipes, system updates user embedding based on feedback
4. Subsequent candidates use personalized ranking

### 4. Personalized Recommendations (5+ Swipes)
1. System retrieves remaining candidate items
2. System calculates cosine similarity between user embedding and item embeddings
3. System returns top-ranked candidates by similarity score
4. Every 5 additional swipes, user embedding is refined further

### 5. Completion (30 Right Swipes)
1. Training phase completes
2. Final personalized recommendations can be generated
3. User embedding represents learned preferences

## Configuration

### Environment Variables
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
```

### Embedding Models
- **User Embeddings**: `text-embedding-ada-002` (1536 dimensions)
- **Item Embeddings**: `text-embedding-3-small` (1536 dimensions)

### Learning Parameters
- **Reinforcement Weight**: +0.1 for liked items
- **Discouragement Weight**: -0.05 for disliked items
- **Update Frequency**: Every 5 swipes
- **Personalization Threshold**: 5 right swipes

## Testing

### Run Complete Test Suite
```bash
cd backend/hunter_agent
python test_embedding_workflow.py
```

### Test Components
1. **User Profile Creation**: Creates test user with preferences
2. **User Embedding Generation**: Tests embedding creation and storage
3. **Item Embedding Generation**: Tests item embedding pipeline
4. **Swipe Simulation**: Tests feedback learning mechanism
5. **Personalized Recommendations**: Tests final recommendation generation

## Monitoring and Analytics

### Key Metrics to Track
- Embedding generation time and success rate
- Swipe-to-recommendation latency
- User engagement improvement after personalization kicks in
- Embedding similarity distributions
- Recommendation diversity and accuracy

### Database Queries for Analysis
```sql
-- User embedding evolution
SELECT uuid, version, created_at 
FROM user_embedding 
WHERE uuid = 'user_id' 
ORDER BY version;

-- Item embedding coverage
SELECT COUNT(*) as total_items,
       COUNT(ie.item_id) as items_with_embeddings
FROM item i
LEFT JOIN item_embedding ie ON i.item_id = ie.item_id;

-- Personalization effectiveness
SELECT COUNT(*) as personalized_users
FROM user_embedding ue
JOIN (
  SELECT uuid, COUNT(*) as swipe_count
  FROM user_item 
  WHERE status IN ('swipe_left', 'swipe_right')
  GROUP BY uuid
  HAVING COUNT(*) >= 5
) swipes ON ue.uuid = swipes.uuid;
```

## Future Enhancements

### 1. Advanced Reranking
- Implement temporal decay for older preferences
- Add category-specific preference learning
- Use transformer-based reranking models

### 2. Cross-Domain Learning
- Learn preferences across art categories
- Transfer learning between similar users
- Multi-modal embeddings (text + visual)

### 3. Real-time Optimization
- Dynamic embedding updates during session
- A/B testing for learning parameters
- Contextual recommendations based on time/mood

### 4. Analytics Dashboard
- User preference visualization
- Recommendation performance metrics
- Embedding quality assessment tools

## Troubleshooting

### Common Issues

#### 1. Embeddings Not Generated
- Check OpenAI API key and quota
- Verify database connection and permissions
- Ensure text content is not empty

#### 2. Personalization Not Working
- Check if user has 5+ swipes
- Verify embedding storage in database
- Check for errors in reranking logic

#### 3. Slow Performance
- Optimize embedding queries with proper indexes
- Consider caching frequently accessed embeddings
- Batch process embedding generation

#### 4. Database Connection Issues
- Verify Supabase credentials
- Check network connectivity
- Ensure proper table creation

### Debug Commands
```bash
# Check user embedding
python -c "from backend.db.supabase_client import get_user_embedding; print(get_user_embedding('user_uuid'))"

# Check item embeddings
python -c "from backend.db.supabase_client import get_items_with_embeddings; print(len(get_items_with_embeddings(['item1', 'item2'])))"

# Test reranker
python -c "from backend.hunter_agent.reranker import get_personalized_candidates; print(get_personalized_candidates('user_uuid', 5))"
```

## Implementation Notes

This implementation provides a robust foundation for embedding-based recommendations while maintaining backward compatibility with the existing system. The modular design allows for easy experimentation with different embedding models, learning parameters, and reranking strategies.