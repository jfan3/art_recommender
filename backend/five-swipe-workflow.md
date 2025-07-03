# 5-Swipe Workflow: From Preference Learning to 3-Month Art Journey

This document describes the enhanced workflow where users complete their preference learning after just 5 swipes, which then triggers the generation of a personalized 3-month art journey plan.

## Overview

The new workflow reduces the swipe requirement from 30 to 5 swipes, making the user experience faster while still gathering enough preference data to generate meaningful recommendations.

```
用户 profile → embedding.py → 用户 embedding
     ↓
初步推荐 → 用户 swipe 5个 → reranker.py → 更新用户 embedding
     ↓
API 检索 top 100 → art_embedding.py → 候选项 embedding
     ↓
最终相似度排序 → plan_agent → 输出 3-month personalized plan
```

## Workflow Steps

### 1. User Profile & Initial Recommendations
- User completes profile via chat interface
- System generates user embedding from profile text
- System retrieves and stores candidate item embeddings
- User begins swiping on initial diverse candidates

### 2. Preference Learning (5 Swipes)
- User swipes on exactly 5 items (mix of likes/dislikes)
- Each swipe is recorded in the database
- After 5th swipe, system triggers preference update

### 3. Embedding Update & Personalization
- System updates user embedding based on 5-swipe feedback
- Liked items get +0.1 weight reinforcement
- Disliked items get -0.05 weight discouragement
- Updated embedding stored with incremented version

### 4. Plan Generation
- System retrieves top 50 personalized candidates using updated embedding
- Candidates ranked by cosine similarity to user embedding
- plan_agent generates 3-month (12-week) plan with medium effort level
- Plan optimizes for diversity and time management

### 5. Plan Presentation
- Frontend automatically transitions to 3-month plan view
- Shows weekly breakdown with statistics
- Displays personalized art journey recommendations

## Technical Implementation

### Backend Changes

#### Enhanced API Endpoint: `POST /api/swipe`
```python
# After exactly 5 total swipes
if total_swipes == 5:
    # Update user embedding based on feedback
    update_user_embedding_from_swipes(user_uuid)
    
    # Get top-ranked candidates
    personalized_candidates = get_personalized_candidates(user_uuid, limit=50)
    
    # Generate 3-month plan
    plan_result = generate_three_month_plan(user_uuid, personalized_candidates)
    
    return {
        "success": True,
        "swipes_complete": True, 
        "plan_generated": plan_result.get("success", False),
        "plan_items": plan_result.get("plan_items", 0)
    }
```

#### New Function: `generate_three_month_plan()`
- Formats candidates for plan_agent compatibility
- Calls `generate_smart_weekly_plan()` from plan_agent/main.py
- Generates 12-week plan with medium effort level
- Saves plan to user-specific JSON file
- Returns plan statistics and success status

#### New Endpoint: `GET /api/user_plan/{user_uuid}`
- Retrieves user's generated 3-month plan
- Returns plan existence status and full weekly breakdown
- Calculates plan statistics (items, time, weeks)

### Frontend Changes

#### Enhanced SwipeFlow Component
```typescript
// New state for 5-swipe completion
const [swipesComplete, setSwipesComplete] = useState(false);

// Handle 5-swipe completion response
if (data.swipes_complete && data.plan_generated) {
  toast.success(`Generated ${data.plan_items} personalized recommendations for your 3-month art journey.`);
  setSwipesComplete(true);
  return;
}

// Conditional rendering
if (swipesComplete) {
  return <ThreeMonthPlan userUuid={userUuid} />;
}
```

#### New Component: ThreeMonthPlan
- Fetches and displays user's 3-month plan
- Shows plan statistics and weekly breakdown
- Responsive design with arteme styling
- Interactive item cards with source links

### Plan Agent Integration

#### Data Flow
1. **Candidate Formatting**: Hunter agent formats personalized candidates for plan_agent
2. **Plan Generation**: Calls `generate_smart_weekly_plan()` with 12 weeks, medium effort
3. **Plan Storage**: Saves to `backend/plan_agent/user_plan_{uuid}.json`
4. **Plan Retrieval**: Frontend fetches plan via API endpoint

#### Plan Configuration
- **Duration**: 3 months (12 weeks)
- **Effort Level**: Medium (12 hours/week)
- **Candidate Limit**: Top 50 personalized recommendations
- **Diversity**: Optimized across different art categories

## User Experience Flow

### 1. Onboarding (1-2 minutes)
```
Chat Interface → Profile Creation → Candidate Generation → Start Swiping
```

### 2. Preference Learning (30 seconds)
```
Swipe 1 → Swipe 2 → Swipe 3 → Swipe 4 → Swipe 5 → Embedding Update
```

### 3. Plan Generation (5 seconds)
```
Personalized Ranking → Plan Agent → 3-Month Plan → Plan Display
```

### 4. Art Journey (3 months)
```
Weekly Plan View → Individual Item Details → Progress Tracking
```

## Benefits of 5-Swipe Approach

### User Experience
- **Faster onboarding**: Complete preference learning in 30 seconds
- **Reduced friction**: Lower commitment threshold than 30 swipes
- **Immediate value**: Get personalized plan quickly
- **Better engagement**: Clear progression to meaningful outcome

### Technical Advantages
- **Efficient learning**: 5 swipes provide sufficient signal for preference learning
- **Reduced computational load**: Fewer swipes to process
- **Faster iteration**: Users can restart if unsatisfied with plan
- **Better conversion**: Higher completion rate expected

### Business Impact
- **Higher completion rates**: Lower barrier to entry
- **Faster time-to-value**: Users see results immediately
- **Better retention**: Users committed to 3-month journey
- **Clear value proposition**: Concrete deliverable (personalized plan)

## Configuration Options

### Swipe Threshold
- **Current**: 5 swipes
- **Configurable**: Can be adjusted based on data quality analysis
- **Minimum**: 3 swipes (for basic preference signal)
- **Maximum**: 10 swipes (for enhanced accuracy)

### Plan Parameters
- **Duration**: 3 months (could be 1-6 months)
- **Effort Level**: Medium (could be user-selectable: chill/medium/intense)
- **Candidate Pool**: Top 50 (could be 25-100 based on user preference)

### Embedding Updates
- **Initial Update**: After 5 swipes
- **Continuous Learning**: Every additional 5 swipes
- **Reinforcement**: +0.1 for likes, -0.05 for dislikes
- **Normalization**: L2 normalization after each update

## Monitoring & Analytics

### Key Metrics
- **5-swipe completion rate**: Percentage who complete initial preference learning
- **Plan generation success rate**: Technical success of plan creation
- **Plan engagement**: User interaction with generated plans
- **Plan satisfaction**: User feedback on plan quality

### A/B Testing Opportunities
- **Swipe threshold**: Test 3 vs 5 vs 7 swipes
- **Plan duration**: Test 1 vs 2 vs 3 month plans
- **Effort levels**: Test different default effort levels
- **Candidate pool size**: Test 25 vs 50 vs 100 candidates

## Error Handling

### Swipe Processing Failures
- Graceful degradation to original 30-swipe flow
- User notification with retry option
- Fallback plan generation from profile embedding

### Plan Generation Failures
- Error message with option to regenerate
- Fallback to displaying top candidates list
- Support contact information for technical issues

### Plan Display Failures
- Loading states with progress indicators
- Retry mechanisms with exponential backoff
- Offline plan caching for return visits

## Future Enhancements

### Dynamic Swipe Requirements
- Adaptive threshold based on confidence in preference learning
- Early completion if high confidence after 3 swipes
- Extended learning if low confidence after 5 swipes

### Interactive Plan Editing
- Allow users to modify generated plans
- Add/remove items from weekly schedules
- Adjust effort levels and durations

### Social Features
- Share plans with friends
- Community plan templates
- Collaborative art journeys

### Progress Tracking
- Weekly check-ins and progress updates
- Achievement badges and milestones
- Recommendation refinement based on completion

## Testing

### Unit Tests
- Test swipe threshold detection
- Test embedding update logic
- Test plan generation pipeline
- Test error handling scenarios

### Integration Tests
- Test full 5-swipe workflow end-to-end
- Test plan agent integration
- Test frontend state transitions
- Test API endpoint interactions

### User Testing
- A/B test 5-swipe vs 30-swipe completion rates
- Usability testing of plan interface
- Satisfaction surveys on plan quality
- Long-term engagement tracking

This 5-swipe workflow represents a significant improvement in user experience while maintaining the sophisticated recommendation quality of the original system.