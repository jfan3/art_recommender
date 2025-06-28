# Plan Agent

A smart media planning system that generates personalized media consumption plans with customizable duration, effort levels, diversity optimization, and user confirmation workflow.

## Features

- **Flexible Duration**: Choose from 1, 2, or 3 month plans
- **Effort Levels**: Chill (6h/week), Medium (12h/week), or Intense (18h/week)
- **Smart Weekly Planning**: Generates plans with time budget considerations
- **Diversity Optimization**: Ensures variety across different media types
- **Interactive Editing**: Add, remove, or shuffle items in your plan
- **User Confirmation**: Final confirmation workflow before saving
- **Quick Confirmation**: Fast confirm option for users satisfied with recommendations
- **Plan Statistics**: Comprehensive analysis of your media plan
- **JSON Export**: Save plans for future reference
- **Time Estimates**: Realistic time commitments for different media types

## Plan Customization Options

### Duration Options
- **1 Month (4 weeks)**: Quick cultural journey - 24-72 hours total
- **2 Months (8 weeks)**: Balanced cultural exploration - 48-144 hours total  
- **3 Months (12 weeks)**: Comprehensive cultural immersion - 72-216 hours total

### Effort Levels
- **Chill**: 6 hours/week (relaxed pace)
  - 1 month: 24 hours total
  - 2 months: 48 hours total
  - 3 months: 72 hours total

- **Medium**: 12 hours/week (balanced pace)
  - 1 month: 48 hours total
  - 2 months: 96 hours total
  - 3 months: 144 hours total

- **Intense**: 18 hours/week (intensive pace)
  - 1 month: 72 hours total
  - 2 months: 144 hours total
  - 3 months: 216 hours total

## Supported Media Types

- **Movie**: 2 hours (average movie length)
- **Book**: 8 hours (weekly reading time)
- **Music**: 1 hour (album listening session)
- **Art**: 3 hours (museum/exhibition visit)
- **Poetry**: 2 hours (poetry reading session)
- **Musicals**: 3 hours (musical performance)
- **Podcast**: 1 hour (podcast episode)
- **Web**: 1 hour (web content browsing)

## Usage

### Interactive Mode
```bash
python main.py
```
This will:
1. Let you choose plan duration (1-3 months)
2. Let you select effort level (chill/medium/intense)
3. Load ranked candidates from `ranked_candidates_sample.json`
4. Generate a smart weekly plan
5. Allow interactive editing (add/remove items)
6. Present final confirmation
7. Save the plan to `final_media_plan.json`

### Quick Confirmation Options

If you're satisfied with the recommendations, you can use quick confirmation:

1. **During Editing**: Type `confirm` to skip directly to saving
2. **During Final Confirmation**: Type `quick` to skip detailed review

### Testing
```bash
python test_plan_agent.py
```
Runs comprehensive tests to verify all functionality.

### Demo
```bash
python demo_plan_agent.py
```
Shows a complete workflow demonstration.

### Quick Demo
```bash
python quick_demo.py
```
Demonstrates the quick confirmation feature.

### Advanced Demo
```bash
python advanced_demo.py
```
Shows all customization options and generates sample plans for each configuration.

## File Structure

```
plan_agent/
├── main.py                          # Main application
├── test_plan_agent.py              # Test suite
├── demo_plan_agent.py              # Demo script
├── quick_demo.py                   # Quick confirmation demo
├── advanced_demo.py                # Advanced customization demo
├── ranked_candidates_sample.json   # Sample input data (42 items)
├── final_media_plan.json          # Generated plan (after confirmation)
└── README.md                       # This file
```

## Interactive Commands

When using the interactive mode, you can use these commands:

- `remove [number]` - Remove item by its number
- `add` - Add a new item to the plan
- `shuffle` - Regenerate plan with same items
- `confirm` - Quick confirm and save (skip editing)
- `quit` - Exit without saving

During final confirmation:
- `yes` - Confirm and save the plan
- `quick` - Quick confirm (skip detailed review)
- `no` - Go back to editing
- `preview` - See the full plan again

## Input Format

The system expects a JSON file with ranked candidates in this format:

```json
[
  {
    "title": "Item Title",
    "type": "movie",
    "description": "Item description",
    "source_url": "https://example.com",
    "image_url": "https://example.com/image.jpg",
    "score": 0.95,
    "category": "movie"
  }
]
```

## Output Format

The generated plan is saved as a JSON file with this structure:

```json
{
  "Week 1": [
    {
      "title": "Item Title",
      "type": "movie",
      "description": "Item description",
      "source_url": "https://example.com",
      "image_url": "https://example.com/image.jpg",
      "score": 0.95,
      "category": "movie",
      "plan_id": 1
    }
  ]
}
```

## Key Functions

### `select_plan_options()`
Handles user selection of duration and effort level.

### `generate_smart_weekly_plan(candidates, num_weeks, effort_level)`
Generates a smart weekly plan with diversity and time considerations.

### `calculate_weekly_time_budget(effort_level)`
Returns weekly time budget based on effort level.

### `user_final_confirmation(plan)`
Handles the user confirmation process with options to:
- Confirm and save the plan
- Quick confirm (skip detailed review)
- Go back to editing
- Preview the full plan

### `display_final_summary(plan)`
Shows comprehensive statistics including:
- Total items and time commitment
- Media type breakdown
- Top 5 recommendations

### `save_final_plan(plan, filename)`
Saves the final plan to a JSON file.

## Algorithm Details

The planning algorithm:
1. Sorts candidates by score (highest first)
2. Allocates items to weeks based on time budget (varies by effort level)
3. Applies diversity penalties to avoid repetition
4. Ensures even distribution across weeks
5. Optimizes for both quality (score) and variety (diversity)

## Time Budget by Effort Level

- **Chill**: 6 hours per week
- **Medium**: 12 hours per week  
- **Intense**: 18 hours per week

## Dependencies

- Python 3.6+
- Standard library modules: `json`, `math`, `random`, `typing`

## Example Output

```
============================================================
               YOUR SMART MEDIA PLAN
============================================================

--- Week 1 ---
  1. [MOVIE] Eternal Sunshine of the Spotless Mind
      Score: 0.95 | Time: 2h
  2. [BOOK] The House of the Spirits by Isabel Allende
      Score: 0.92 | Time: 8h
  3. [MUSIC] Blade Runner 2049 Soundtrack
      Score: 0.89 | Time: 1h
  Week total: 11h / 12h

Total plan time: 64h over 12 weeks
Average per week: 5.3h
Effort level: Medium
```

## Contributing

To extend the system:
1. Add new media types to `get_media_time_estimate()`
2. Modify the diversity algorithm in `generate_smart_weekly_plan()`
3. Update the confirmation workflow in `user_final_confirmation()`
4. Add new analysis features to `display_final_summary()`
5. Add new effort levels to `calculate_weekly_time_budget()` 