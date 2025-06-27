import json
import math

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

def generate_weekly_plan(candidates, num_weeks=12):
    """Generates a 3-month (12-week) plan from the candidates."""
    # This is a simple distribution. We can make it smarter later.
    items_per_week = math.ceil(len(candidates) / num_weeks)
    weekly_plan = {}
    for i in range(num_weeks):
        week = i + 1
        start_index = i * items_per_week
        end_index = start_index + items_per_week
        weekly_plan[f"Week {week}"] = candidates[start_index:end_index]
    return weekly_plan

def display_plan(plan):
    """Displays the plan in a readable format."""
    print("\n" + "="*50)
    print(" " * 15 + "YOUR 3-MONTH MEDIA PLAN")
    print("="*50 + "\n")
    
    item_number = 1
    for week, items in plan.items():
        print(f"--- {week} ---")
        if not items:
            print("  (Nothing planned for this week.)")
        for item in items:
            print(f"  {item_number}. [{item.get('type', 'N/A').upper()}] {item.get('title')}")
            item['plan_id'] = item_number # Assign a temporary ID for removal
            item_number += 1
        print("-" * 15)

def manual_curation_loop(plan):
    """Handles the user interaction loop for managing the plan."""
    # Convert the plan to a list of items for easier manipulation
    all_items = [item for week_items in plan.values() for item in week_items]
    
    while True:
        # Re-generate and display the plan each time to get correct numbering
        current_plan = generate_weekly_plan(all_items)
        display_plan(current_plan)
        
        print("\nWhat would you like to do?")
        action = input("Enter 'remove [number]', 'add', or 'quit': ").lower().strip()
        
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

        elif action == "quit":
            print("\nExiting plan management. Here is your final plan:")
            final_plan = generate_weekly_plan(all_items)
            display_plan(final_plan)
            # We could also save the 'all_items' list to a file here
            break
        else:
            print("\nInvalid command. Please try again.")
            
    return all_items

def main():
    """Main function to run the plan agent."""
    candidates = load_ranked_candidates("backend/plan_agent/ranked_candidates_sample.json")
    if not candidates:
        print("No candidates loaded. Exiting.")
        return
        
    # Generate the initial plan from all candidates
    weekly_plan = generate_weekly_plan(candidates)
    
    # Enter the interactive loop
    final_candidates = manual_curation_loop(weekly_plan)
    
    # We could do something with the final plan here, like saving it.
    print(f"\nPlan agent finished. You have {len(final_candidates)} items in your final plan.")


if __name__ == "__main__":
    main() 