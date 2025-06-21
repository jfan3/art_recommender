import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/v1/profiler/chat"
URL = f"{BASE_URL}{ENDPOINT}"

def main():
    """
    Main function to run the interactive chat session with the Profiler Agent.
    """
    print("--- Starting Chat with Profiler Agent ---")
    print("Type 'quit' at any time to exit.")

    # Initialize session variables
    session_id = "cli-session-1"
    user_id = None
    conversation_history = []
    profiling_complete = False
    
    # Start the conversation
    message = "Hi"

    while not profiling_complete:
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
            "conversation_history": conversation_history
        }

        try:
            response = requests.post(URL, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            data = response.json()
            
            # Update state from response
            user_id = data.get("user_id")
            agent_response = data.get("agent_response")
            profiling_complete = data.get("profiling_complete", False)

            print(f"\n🤖 Agent: {agent_response}")

            # Add to history
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append({"role": "agent", "content": agent_response})


            if profiling_complete:
                print("\n--- Profiling Complete ---")
                print("The agent has finished collecting your information.")
                break

            # Get next message from user
            message = input("🙂 You: ")
            if message.lower() == 'quit':
                print("--- Exiting session ---")
                break

        except requests.exceptions.RequestException as e:
            print(f"\n--- Error ---")
            print(f"Could not connect to the Profiler Agent service at {URL}.")
            print("Please make sure the FastAPI server is running.")
            print(f"Error details: {e}")
            break

if __name__ == "__main__":
    main() 