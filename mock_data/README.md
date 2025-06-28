# Art Recommender Database Schema & Mock Data

This directory contains mock JSON files for the three main tables in the Art Recommender system.

## Database Schema

### 1. User Profile Table (`user_profiles.json`)

**Fields:**
- `uuid` (string): Unique identifier for the user
- `past_favorite_work` (array): List of user's favorite works
- `taste_genre` (string): User's preferred genres/tastes
- `current_obsession` (array): User's current interests/obsessions
- `state_of_mind` (string): User's current emotional/mental state
- `future_aspirations` (string): User's future goals/aspirations
- `complete` (boolean): Whether the profile is complete
- `created_at` (string): ISO timestamp when profile was created
- `updated_at` (string): ISO timestamp when profile was last updated

### 2. Item Table (`items.json`)

**Fields:**
- `item_id` (string): Unique identifier for the item
- `item_name` (string): Name/title of the item
- `description` (string): Description of the item
- `source_url` (string): URL to the original source
- `image_url` (string): URL to the item's image
- `category` (string): Category of the item
- `creator` (string): Creator/author/artist of the item
- `release_date` (string): Release date of the item
- `metadata` (object): Category-specific metadata

**Categories and Metadata Schemas:**

#### Movies (`category: "movie"`)
```json
{
  "original_language": "en",
  "genre": "28, 18, 878",
  "country": "US",
  "rating": "7.8",
  "tags": "psychological thriller, sci-fi, drama",
  "awards": "Sundance Film Festival"
}
```

#### Books (`category: "book"`)
```json
{
  "genre": "Fiction, Classics, Romance",
  "language": "en",
  "country": "US",
  "tags": "american literature, jazz age, tragedy",
  "rating": "4.2",
  "awards": "Modern Library 100 Best Novels"
}
```

#### Music (`category: "music"`)
```json
{
  "genre": "Rock, Progressive Rock",
  "tags": "classic rock, opera, epic",
  "country": "GB",
  "language": "en",
  "rating": "95",
  "mood": "epic, dramatic",
  "awards": "Grammy Hall of Fame"
}
```

#### Art (`category: "art"`)
```json
{
  "displayed_link": "moma.org",
  "position": "1",
  "tags": "post-impressionism, landscape, night",
  "rating": "9.5",
  "mood": "contemplative, dreamy",
  "domain": "moma.org",
  "quality_score": "high"
}
```

#### Poetry (`category: "poetry"`)
```json
{
  "displayed_link": "poetryfoundation.org",
  "position": "1",
  "tags": "american poetry, choices, nature",
  "rating": "9.0",
  "mood": "contemplative",
  "domain": "poetryfoundation.org",
  "quality_score": "high"
}
```

#### Musicals (`category: "musical"`)
```json
{
  "displayed_link": "broadway.com",
  "position": "1",
  "tags": "hip-hop, history, revolutionary",
  "rating": "9.8",
  "mood": "energetic, revolutionary",
  "domain": "broadway.com",
  "quality_score": "high"
}
```

#### Podcasts (`category: "podcast"`)
```json
{
  "displayed_link": "thisamericanlife.org",
  "position": "1",
  "tags": "storytelling, journalism, human interest",
  "rating": "9.2",
  "mood": "thoughtful, engaging",
  "domain": "thisamericanlife.org",
  "quality_score": "high"
}
```

### 3. User Item Table (`user_items.json`)

**Fields:**
- `uuid` (string): User's unique identifier (foreign key to user_profiles)
- `item_id` (string): Item's unique identifier (foreign key to items)
- `status` (string): Current status of the user-item interaction
- `last_update_date` (string): ISO timestamp when status was last updated

**Status Values:**
1. `candidate` - Item returned from initial hunter agent search
2. `swipe_left` - User swiped left (disliked)
3. `swipe_right` - User swiped right (liked)
4. `shortlisted` - Item shortlisted to be included in calendar
5. `confirmed` - Item listed on the calendar
6. `like` - User expressed like based on past experience
7. `dislike` - User expressed dislike based on past experience

## Mock Data Overview

The mock data includes:

- **5 user profiles** with different tastes and interests
- **10 items** across all categories (movies, books, music, art, poetry, musicals, podcasts)
- **25 user-item interactions** showing various statuses and user behaviors

## Data Sources

The item data structure is based on the actual APIs used in the hunter_agent:
- **Movies**: TMDB API
- **Books**: OpenLibrary API
- **Music**: Spotify API
- **Art/Poetry/Musicals/Podcasts**: SerpAPI (Google Search) with quality site filtering

## Usage

These mock files can be used for:
- Testing the recommendation system
- Developing the frontend interface
- Database schema validation
- API endpoint development
- User experience testing

## Next Steps

After reviewing these mock files, you can proceed to:
1. Create the actual database tables
2. Implement data import/export functions
3. Build API endpoints for CRUD operations
4. Develop the frontend interface
5. Integrate with the existing hunter_agent system 