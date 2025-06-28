import json
import math
import random
from typing import List, Dict

def load_ranked_candidates(path="ranked_candidates_sample.json"):
    """Loads the list of ranked candidates from a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError: 
        print(f"Error: Could not find the file at {path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode the JSON file at {path}")
        return []

def get_media_time_estimate(item_type: str) -> int:
    """Estimate time commitment for different media types (in hours)."""
    time_estimates = {
        "movie": 2,           # Average movie length 
        "book": 8,            # Weekly reading time (1 hour/day)
        "music": 1,           # Album listening session 
        "art": 3,             # Museum/exhibition visit 
        "poetry": 2,          # Poetry reading session 
        "musicals": 3,        # Musical performance 
        "podcasts": 1,        # Podcast episode 
        "web": 1              # Web content browsing 
    }
    return time_estimates.get(item_type.lower(), 1)

def calculate_weekly_time_budget(effort_level: str = "medium") -> int:
    """Calculate reasonable weekly time budget for media consumption (in hours)."""
    effort_levels = {
        "chill": 6,      # 6 hours per week - relaxed pace
        "medium": 12,    # 12 hours per week - balanced pace
        "intense": 18    # 18 hours per week - intensive pace
    }
    return effort_levels.get(effort_level.lower(), 12)

def get_plan_duration_weeks(duration_months: int) -> int:
    """Convert months to weeks."""
    return duration_months * 4  # Approximate 4 weeks per month

def select_plan_options():
    """Let user select plan duration and effort level."""
    print("\n" + "="*60)
    print(" " * 15 + "PLAN CUSTOMIZATION")
    print("="*60)
    
    # Duration selection
    print("\nSelect plan duration:")
    print("1. 1 month (4 weeks) - Quick cultural journey")
    print("2. 2 months (8 weeks) - Balanced cultural exploration")
    print("3. 3 months (12 weeks) - Comprehensive cultural immersion")
    
    while True:
        try:
            duration_choice = input("\nEnter your choice (1-3): ").strip()
            if duration_choice in ['1', '2', '3']:
                duration_months = int(duration_choice)
                break
            else:
                print("Please enter 1, 2, or 3")
        except ValueError:
            print("Please enter a valid number")
    
    # Effort level selection
    print("\nSelect effort level:")
    print("1. Chill - 6 hours/week (relaxed pace)")
    print("2. Medium - 12 hours/week (balanced pace)")
    print("3. Intense - 18 hours/week (intensive pace)")
    
    while True:
        try:
            effort_choice = input("\nEnter your choice (1-3): ").strip()
            if effort_choice == '1':
                effort_level = "chill"
                break
            elif effort_choice == '2':
                effort_level = "medium"
                break
            elif effort_choice == '3':
                effort_level = "intense"
                break
            else:
                print("Please enter 1, 2, or 3")
        except ValueError:
            print("Please enter a valid number")
    
    weeks = get_plan_duration_weeks(duration_months)
    weekly_budget = calculate_weekly_time_budget(effort_level)
    total_budget = weekly_budget * weeks
    
    print(f"\nSelected plan:")
    print(f"   Duration: {duration_months} month(s) ({weeks} weeks)")
    print(f"   Effort level: {effort_level.title()}")
    print(f"   Weekly time budget: {weekly_budget} hours")
    print(f"   Total time commitment: {total_budget} hours")
    
    return duration_months, effort_level, weeks, weekly_budget

def generate_smart_weekly_plan(candidates: List[Dict], num_weeks: int = 12, effort_level: str = "medium") -> Dict:
    """Generates a smart plan with diversity and time considerations."""
    
    # Sort candidates by score (highest first)
    sorted_candidates = sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)
    
    weekly_plan = {}
    weekly_time_budget = calculate_weekly_time_budget(effort_level)
    
    # Track what's been assigned to avoid repetition
    assigned_items = []
    weekly_type_counts = {}  # Track media types per week
    
    # Calculate total available time and target items per week
    total_available_time = weekly_time_budget * num_weeks
    total_items = len(sorted_candidates)
    target_items_per_week = max(1, total_items // num_weeks)
    
    for week in range(1, num_weeks + 1):
        weekly_plan[f"Week {week}"] = []
        weekly_type_counts[week] = {}
        current_week_time = 0
        
        # Calculate remaining weeks and items
        remaining_weeks = num_weeks - week + 1
        remaining_items = total_items - len(assigned_items)
        
        # Adjust weekly budget to ensure even distribution
        if remaining_weeks > 0 and remaining_items > 0:
            # Calculate how many items should be in remaining weeks
            target_remaining_items_per_week = remaining_items / remaining_weeks
            
            # Adjust budget based on remaining items and weeks
            if target_remaining_items_per_week > 1:
                # If we need to fit more items, be more conservative with time
                adjusted_budget = min(weekly_time_budget, 
                                    (total_available_time - sum(get_media_time_estimate(item.get('type', '')) 
                                     for item in assigned_items)) / remaining_weeks)
            else:
                # If we have fewer items, we can be more generous
                adjusted_budget = weekly_time_budget
        else:
            adjusted_budget = weekly_time_budget
        
        # Try to fill each week with diverse content
        items_added_this_week = 0
        max_items_per_week = min(8, target_items_per_week + 3)  # Allow more flexibility for different effort levels
        
        while (current_week_time < adjusted_budget and 
               sorted_candidates and 
               items_added_this_week < max_items_per_week):
            
            best_item = None
            best_score = -1
            
            # Find the best item that fits time budget and diversity requirements
            for i, item in enumerate(sorted_candidates):
                if item in assigned_items:
                    continue
                    
                item_type = item.get('type', 'unknown').lower()
                item_time = get_media_time_estimate(item_type)
                
                # Check if item fits in time budget
                if current_week_time + item_time > adjusted_budget:
                    continue
                
                # Calculate diversity score
                diversity_penalty = 0
                if item_type in weekly_type_counts[week]:
                    diversity_penalty = weekly_type_counts[week][item_type] * 0.15
                
                # Calculate final score (original score - diversity penalty)
                final_score = item.get('score', 0) - diversity_penalty
                
                if final_score > best_score:
                    best_score = final_score
                    best_item = (i, item)
            
            # Add the best item to this week
            if best_item:
                index, item = best_item
                item_type = item.get('type', 'unknown').lower()
                
                weekly_plan[f"Week {week}"].append(item)
                assigned_items.append(item)
                current_week_time += get_media_time_estimate(item_type)
                items_added_this_week += 1
                
                # Update type counts
                weekly_type_counts[week][item_type] = weekly_type_counts[week].get(item_type, 0) + 1
                
                # Remove from candidates
                sorted_candidates.pop(index)
            else:
                break
    
    return weekly_plan

def generate_weekly_plan(candidates, num_weeks=12):
    """Legacy function - now calls the smart version."""
    return generate_smart_weekly_plan(candidates, num_weeks)

def display_plan(plan, effort_level="medium"):
    """Displays the plan in a readable format with time estimates."""
    weekly_budget = calculate_weekly_time_budget(effort_level)
    
    print("\n" + "="*60)
    print(" " * 15 + "YOUR SMART MEDIA PLAN")
    print("="*60 + "\n")
    
    item_number = 1
    total_time = 0
    
    for week, items in plan.items():
        print(f"--- {week} ---")
        week_time = 0
        
        if not items:
            print("  (Nothing planned for this week.)")
        else:
            for item in items:
                item_type = item.get('type', 'N/A').upper()
                title = item.get('title', 'Unknown')
                score = item.get('score', 0)
                time_estimate = get_media_time_estimate(item.get('type', ''))
                week_time += time_estimate
                
                print(f"  {item_number}. [{item_type}] {title}")
                print(f"      Score: {score:.2f} | Time: {time_estimate}h")
                item['plan_id'] = item_number
                item_number += 1
            
            print(f"  Week total: {week_time}h / {weekly_budget}h")
            total_time += week_time
        
        print("-" * 20)
    
    print(f"\nTotal plan time: {total_time}h over {len(plan)} weeks")
    print(f"Average per week: {total_time/len(plan):.1f}h")
    print(f"Effort level: {effort_level.title()}")

def analyze_plan_diversity(plan):
    """Analyze the diversity of the generated plan."""
    print("\n" + "="*40)
    print("PLAN DIVERSITY ANALYSIS")
    print("="*40)
    
    all_items = [item for week_items in plan.values() for item in week_items]
    type_counts = {}
    
    for item in all_items:
        item_type = item.get('type', 'unknown').lower()
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
    
    print("Media type distribution:")
    for media_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(all_items)) * 100
        print(f"  {media_type.title()}: {count} items ({percentage:.1f}%)")
    
    # Calculate diversity score (higher is more diverse)
    diversity_score = len(type_counts) / len(all_items) if all_items else 0
    print(f"\nDiversity Score: {diversity_score:.2f} (higher = more diverse)")

def manual_curation_loop(plan, effort_level="medium"):
    """Handles the user interaction loop for managing the plan."""
    # Convert the plan to a list of items for easier manipulation
    all_items = [item for week_items in plan.values() for item in week_items]
    
    while True:
        # Re-generate and display the plan each time to get correct numbering
        current_plan = generate_smart_weekly_plan(all_items, len(plan), effort_level)
        display_plan(current_plan, effort_level)
        analyze_plan_diversity(current_plan)
        
        print("\nWhat would you like to do?")
        action = input("Enter 'remove [number]', 'add', 'shuffle', 'confirm', or 'quit': ").lower().strip()
        
        if action.startswith("remove"):
            try:
                parts = action.split()
                if len(parts) != 2: raise ValueError
                item_to_remove = int(parts[1])
                
                original_count = len(all_items)
                # Filter out the item with the matching plan_id
                all_items = [item for item in all_items if item.get('plan_id') != item_to_remove]
                
                if len(all_items) < original_count:
                    print(f"\nSuccessfully removed item {item_to_remove}.")
                else:
                    print(f"\nItem number {item_to_remove} not found.")
            except (ValueError, IndexError):
                print("\nInvalid 'remove' command. Please use the format: remove [number]")

        elif action == "add":
            print("\n--- Adding a new item ---")
            title = input("Enter title: ")
            item_type = input("Enter type (e.g., movie, book, art): ")
            description = input("Enter a short description: ")
            
            new_item = {
                "title": title,
                "type": item_type,
                "description": description,
                "source_url": "N/A (manual entry)",
                "image_url": "N/A (manual entry)",
                "score": 1.0, # Manually added items get highest priority
                "category": item_type
            }
            
            all_items.append(new_item)
            # Re-sort list so new item appears based on score (at the top)
            all_items.sort(key=lambda x: x.get('score', 0), reverse=True)
            print(f"\nSuccessfully added '{title}' to your plan.")

        elif action == "shuffle":
            print("\nShuffling the plan to create a different arrangement...")
            # Keep the same items but regenerate the plan
            pass

        elif action == "confirm":
            print("\nQuick confirmation selected. Proceeding to save the plan...")
            break

        elif action == "quit":
            print("\nExiting plan management. Here is your final plan:")
            final_plan = generate_smart_weekly_plan(all_items, len(plan), effort_level)
            display_plan(final_plan, effort_level)
            analyze_plan_diversity(final_plan)
            break
        else:
            print("\nInvalid command. Please try again.")
            
    return all_items

def save_final_plan(plan, filename="final_media_plan.json"):
    """Save the final plan to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"Final plan saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving plan: {e}")
        return False

def display_final_summary(plan):
    """Display a comprehensive final summary of the plan."""
    print("\n" + "="*70)
    print(" " * 20 + "FINAL PLAN SUMMARY")
    print("="*70)
    
    all_items = [item for week_items in plan.values() for item in week_items]
    total_time = sum(get_media_time_estimate(item.get('type', '')) for item in all_items)
    
    print(f"\nPLAN STATISTICS:")
    print(f"   Total items: {len(all_items)}")
    print(f"   Total time commitment: {total_time} hours")
    print(f"   Duration: {len(plan)} weeks")
    print(f"   Average per week: {total_time/len(plan):.1f} hours")
    
    # Type breakdown
    type_counts = {}
    for item in all_items:
        item_type = item.get('type', 'unknown').lower()
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
    
    print(f"\nMEDIA TYPE BREAKDOWN:")
    for media_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(all_items)) * 100
        print(f"   {media_type.title()}: {count} items ({percentage:.1f}%)")
    
    # Top recommendations
    top_items = sorted(all_items, key=lambda x: x.get('score', 0), reverse=True)[:5]
    print(f"\nTOP 5 RECOMMENDATIONS:")
    for i, item in enumerate(top_items, 1):
        print(f"   {i}. {item.get('title', 'Unknown')} (Score: {item.get('score', 0):.2f})")
    
    print(f"\nYou're all set! Your personalized media journey begins now.")
    print(f"   Remember to track your progress and enjoy the experience!")

def user_final_confirmation(plan):
    """Handle the final user confirmation process."""
    print("\n" + "="*60)
    print(" " * 15 + "FINAL CONFIRMATION")
    print("="*60)
    
    # Show a condensed version of the plan
    all_items = [item for week_items in plan.values() for item in week_items]
    total_time = sum(get_media_time_estimate(item.get('type', '')) for item in all_items)
    
    print(f"\nYour plan includes {len(all_items)} items over {len(plan)} weeks")
    print(f"Total time commitment: {total_time} hours ({total_time/len(plan):.1f}h/week)")
    
    # Quick preview of first few weeks
    print(f"\nQUICK PREVIEW (First 3 weeks):")
    for week_num in range(1, min(4, len(plan) + 1)):
        week_key = f"Week {week_num}"
        if week_key in plan:
            items = plan[week_key]
            week_time = sum(get_media_time_estimate(item.get('type', '')) for item in items)
            print(f"   Week {week_num}: {len(items)} items ({week_time}h)")
            for item in items[:2]:  # Show first 2 items per week
                print(f"     {item.get('title', 'Unknown')}")
            if len(items) > 2:
                print(f"     ... and {len(items)-2} more")
    
    while True:
        print(f"\nAre you satisfied with this plan?")
        print(f"   Options:")
        print(f"   'yes' - Confirm and save the plan")
        print(f"   'quick' - Quick confirm (skip detailed review)")
        print(f"   'no' - Go back to editing")
        print(f"   'preview' - See the full plan again")
        
        choice = input("\nEnter your choice: ").lower().strip()
        
        if choice in ['yes', 'y']:
            return True
        elif choice == 'quick':
            print("Quick confirmation selected. Saving plan immediately...")
            return True
        elif choice in ['no', 'n']:
            return False
        elif choice == 'preview':
            display_plan(plan)
            analyze_plan_diversity(plan)
        else:
            print("Invalid choice. Please enter 'yes', 'quick', 'no', or 'preview'.")

def show_mode_selection():
    """Show different modes and let user choose."""
    print("\n" + "="*60)
    print(" " * 15 + "PLAN AGENT MODES")
    print("="*60)
    
    print("\nSelect a mode:")
    print("1. Interactive Mode - Create your own personalized plan")
    print("2. Demo Mode - See how the system works")
    print("3. Comparison Mode - View all plan configurations")
    print("4. Quick Demo - Fast workflow demonstration")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            else:
                print("Please enter a number between 1 and 5")
        except ValueError:
            print("Please enter a valid number")

def run_interactive_mode():
    """Run the full interactive mode."""
    print("\n" + "="*60)
    print(" " * 15 + "INTERACTIVE MODE")
    print("="*60)
    
    candidates = load_ranked_candidates("ranked_candidates_sample.json")
    if not candidates:
        print("No candidates loaded. Exiting.")
        return
    
    print("Welcome to the Smart Media Plan Generator!")
    print("This tool will create a personalized media consumption plan based on your preferences.")
    
    # Get user preferences
    duration_months, effort_level, num_weeks, weekly_budget = select_plan_options()
    
    print(f"\nGenerating {duration_months}-month {effort_level} plan with diversity and time considerations...")
    
    # Generate the initial plan from all candidates
    weekly_plan = generate_smart_weekly_plan(candidates, num_weeks, effort_level)
    
    # Enter the interactive loop
    final_candidates = manual_curation_loop(weekly_plan, effort_level)
    
    # Generate final plan from curated candidates
    final_plan = generate_smart_weekly_plan(final_candidates, num_weeks, effort_level)
    
    # User final confirmation
    confirmed = user_final_confirmation(final_plan)
    
    if confirmed:
        # Save the final plan
        save_final_plan(final_plan)
        
        # Display final summary
        display_final_summary(final_plan)
        
        print(f"\nCongratulations! Your personalized media plan is ready.")
        print(f"   You can find the complete plan in 'final_media_plan.json'")
    else:
        print(f"\nGoing back to plan editing...")
        # Re-enter the editing loop
        final_candidates = manual_curation_loop(final_plan, effort_level)
        final_plan = generate_smart_weekly_plan(final_candidates, num_weeks, effort_level)
        
        # Try confirmation again
        if user_final_confirmation(final_plan):
            save_final_plan(final_plan)
            display_final_summary(final_plan)
            print(f"\nCongratulations! Your personalized media plan is ready.")
        else:
            print(f"\nPlan creation cancelled. You can run the program again to start over.")

def run_demo_mode():
    """Run the demo mode showing complete workflow."""
    print("\n" + "="*60)
    print(" " * 15 + "DEMO MODE")
    print("="*60)
    
    # Show features
    show_plan_features()
    
    # Run complete workflow demo
    demo_complete_workflow()

def show_plan_features():
    """Show the key features of the plan agent."""
    print("\n" + "="*60)
    print("PLAN AGENT FEATURES")
    print("="*60)
    
    features = [
        "Flexible duration options (1, 2, or 3 months)",
        "Three effort levels (Chill, Medium, Intense)",
        "Smart weekly planning with time budget considerations",
        "Diversity optimization across media types",
        "Interactive plan editing (add/remove items)",
        "User confirmation workflow",
        "Quick confirmation options",
        "Plan statistics and analysis",
        "JSON export functionality",
        "Time estimates for different media types",
        "Score-based prioritization"
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"{i}. {feature}")
    
    print(f"\nMedia types supported:")
    media_types = ["Movie", "Book", "Music", "Art", "Poetry", "Musicals", "Podcast", "Web"]
    for media_type in media_types:
        print(f"   - {media_type}")

def demo_complete_workflow():
    """Demonstrate the complete plan_agent workflow."""
    print("\n" + "="*60)
    print("PLAN AGENT - COMPLETE WORKFLOW DEMO")
    print("="*60)
    
    # Step 1: Load candidates
    print("\nStep 1: Loading ranked candidates...")
    candidates = load_ranked_candidates("ranked_candidates_sample.json")
    if not candidates:
        print("Error: Could not load candidates")
        return
    
    print(f"Loaded {len(candidates)} candidates successfully")
    
    # Step 2: Generate initial plan
    print("\nStep 2: Generating smart weekly plan...")
    plan = generate_smart_weekly_plan(candidates, 12, "medium")
    print("Plan generated successfully")
    
    # Step 3: Display plan
    print("\nStep 3: Displaying generated plan...")
    display_plan(plan, "medium")
    analyze_plan_diversity(plan)
    
    # Step 4: User confirmation (simulated)
    print("\nStep 4: User confirmation process...")
    print("(In real usage, this would be interactive)")
    
    # Simulate user confirming the plan
    confirmed = True  # For demo purposes
    
    if confirmed:
        print("User confirmed the plan")
        
        # Step 5: Save final plan
        print("\nStep 5: Saving final plan...")
        if save_final_plan(plan, "demo_plan.json"):
            print("Plan saved successfully")
        
        # Step 6: Display final summary
        print("\nStep 6: Displaying final summary...")
        display_final_summary(plan)
        
        print("\nDemo completed successfully!")
        print("Check 'demo_plan.json' for the saved plan")
    else:
        print("User rejected the plan (would go back to editing)")

def run_comparison_mode():
    """Run the comparison mode showing all configurations."""
    print("\n" + "="*60)
    print(" " * 15 + "COMPARISON MODE")
    print("="*60)
    
    # Show comparisons
    show_effort_level_comparison()
    show_duration_options()
    
    # Demo different plans
    demo_different_plans()

def show_effort_level_comparison():
    """Show comparison between different effort levels."""
    print("\n" + "="*60)
    print("EFFORT LEVEL COMPARISON")
    print("="*60)
    
    effort_levels = ["chill", "medium", "intense"]
    
    print("\nWeekly Time Budgets:")
    for effort in effort_levels:
        budget = calculate_weekly_time_budget(effort)
        print(f"   {effort.title()}: {budget} hours/week")
    
    print("\nMonthly Time Commitments:")
    for effort in effort_levels:
        budget = calculate_weekly_time_budget(effort)
        monthly = budget * 4
        print(f"   {effort.title()}: {monthly} hours/month")
    
    print("\n3-Month Total Commitments:")
    for effort in effort_levels:
        budget = calculate_weekly_time_budget(effort)
        total = budget * 12
        print(f"   {effort.title()}: {total} hours total")

def show_duration_options():
    """Show different duration options."""
    print("\n" + "="*60)
    print("DURATION OPTIONS")
    print("="*60)
    
    durations = [1, 2, 3]
    effort_levels = ["chill", "medium", "intense"]
    
    print("\nTime Commitments by Duration and Effort:")
    print("Duration | Chill | Medium | Intense")
    print("-" * 40)
    
    for duration in durations:
        weeks = get_plan_duration_weeks(duration)
        chill_total = calculate_weekly_time_budget("chill") * weeks
        medium_total = calculate_weekly_time_budget("medium") * weeks
        intense_total = calculate_weekly_time_budget("intense") * weeks
        
        print(f"{duration} month(s) | {chill_total:5.0f}h | {medium_total:6.0f}h | {intense_total:7.0f}h")

def demo_different_plans():
    """Demonstrate different plan configurations."""
    print("\n" + "="*60)
    print("PLAN CONFIGURATION EXAMPLES")
    print("="*60)
    
    # Load candidates
    candidates = load_ranked_candidates("ranked_candidates_sample.json")
    print(f"Loaded {len(candidates)} candidates")
    
    # Demo configurations
    configurations = [
        {"duration": 1, "effort": "chill", "name": "Quick Chill"},
        {"duration": 2, "effort": "medium", "name": "Balanced Medium"},
        {"duration": 3, "effort": "intense", "name": "Comprehensive Intense"}
    ]
    
    for config in configurations:
        print(f"\n" + "="*50)
        print(f"EXAMPLE: {config['name']} Plan")
        print("="*50)
        
        duration_months = config["duration"]
        effort_level = config["effort"]
        num_weeks = get_plan_duration_weeks(duration_months)
        weekly_budget = calculate_weekly_time_budget(effort_level)
        total_budget = weekly_budget * num_weeks
        
        print(f"Configuration:")
        print(f"   Duration: {duration_months} month(s) ({num_weeks} weeks)")
        print(f"   Effort level: {effort_level.title()}")
        print(f"   Weekly budget: {weekly_budget} hours")
        print(f"   Total budget: {total_budget} hours")
        
        # Generate plan
        plan = generate_smart_weekly_plan(candidates, num_weeks, effort_level)
        
        # Show statistics
        all_items = [item for week_items in plan.values() for item in week_items]
        total_time = sum(get_media_time_estimate(item.get('type', '')) for item in all_items)
        
        print(f"\nPlan Statistics:")
        print(f"   Items included: {len(all_items)}")
        print(f"   Time utilized: {total_time}h / {total_budget}h ({total_time/total_budget*100:.1f}%)")
        print(f"   Average per week: {total_time/num_weeks:.1f}h")

def run_quick_demo_mode():
    """Run the quick demo mode."""
    print("\n" + "="*60)
    print(" " * 15 + "QUICK DEMO MODE")
    print("="*60)
    
    # Show usage options
    show_usage_options()
    
    # Run quick confirmation demo
    quick_confirmation_demo()

def show_usage_options():
    """Show different usage options."""
    print("\n" + "="*50)
    print("USAGE OPTIONS")
    print("="*50)
    
    print("\nOption 1: Full Interactive Mode")
    print("   python main.py (then select mode 1)")
    print("   - Full editing capabilities")
    print("   - Detailed confirmation process")
    
    print("\nOption 2: Quick Confirmation")
    print("   python main.py (then select mode 1)")
    print("   - Type 'confirm' when plan is shown")
    print("   - Skip directly to saving")
    
    print("\nOption 3: Quick Final Confirmation")
    print("   python main.py (then select mode 1)")
    print("   - Type 'quick' during final confirmation")
    print("   - Skip detailed review and save immediately")

def quick_confirmation_demo():
    """Demonstrate the quick confirmation workflow."""
    print("\n" + "="*50)
    print("QUICK CONFIRMATION DEMO")
    print("="*50)
    
    # Load and generate plan
    print("\n1. Loading candidates and generating plan...")
    candidates = load_ranked_candidates("ranked_candidates_sample.json")
    plan = generate_smart_weekly_plan(candidates, 12, "medium")
    
    print(f"Generated plan with {len([item for week_items in plan.values() for item in week_items])} items")
    
    # Show plan overview
    print("\n2. Plan overview:")
    display_plan(plan, "medium")
    
    # Quick confirmation (simulated)
    print("\n3. Quick confirmation process:")
    print("   User: 'confirm' (in interactive mode)")
    print("   System: 'Quick confirmation selected. Proceeding to save the plan...'")
    
    # Save plan
    print("\n4. Saving plan...")
    if save_final_plan(plan, "quick_demo_plan.json"):
        print("   Plan saved successfully!")
    
    # Show final summary
    print("\n5. Final summary:")
    display_final_summary(plan)
    
    print("\n" + "="*50)
    print("Quick confirmation demo completed!")
    print("In real usage, you can:")
    print("- Type 'confirm' during editing to skip to save")
    print("- Type 'quick' during final confirmation to skip detailed review")

def main():
    """Main function to run the plan agent."""
    print("Welcome to the Smart Media Plan Generator!")
    print("="*60)
    
    while True:
        # Show mode selection
        mode = show_mode_selection()
        
        if mode == '1':
            # Interactive Mode
            run_interactive_mode()
        elif mode == '2':
            # Demo Mode
            run_demo_mode()
        elif mode == '3':
            # Comparison Mode
            run_comparison_mode()
        elif mode == '4':
            # Quick Demo Mode
            run_quick_demo_mode()
        elif mode == '5':
            # Exit
            print("\nThank you for using the Smart Media Plan Generator!")
            print("Goodbye!")
            break
        
        # Ask if user wants to continue
        if mode != '5':
            print("\n" + "="*60)
            continue_choice = input("Would you like to try another mode? (y/n): ").lower().strip()
            if continue_choice not in ['y', 'yes']:
                print("\nThank you for using the Smart Media Plan Generator!")
                print("Goodbye!")
                break

if __name__ == "__main__":
    main() 