import requests
import json
import time

# Configuration
BASE_URL = "http://0.0.0.0:8080"
CHAT_ENDPOINT = "/chat"
PROFILES_ENDPOINT = "/profiles"
CONVERSATIONS_ENDPOINT = "/conversations"

def create_profile():
    """Create a new user profile and return the UUID."""
    try:
        response = requests.post(f"{BASE_URL}{PROFILES_ENDPOINT}")
        response.raise_for_status()
        data = response.json()
        return data.get("uuid")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create profile: {e}")
        return None

def send_message(session_id, message, user_uuid=None):
    """Send a message to the profiling agent and return the response."""
    payload = {
        "session_id": session_id,
        "messages": [{"role": "user", "content": message}],
        "user_uuid": user_uuid
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{CHAT_ENDPOINT}",
            json=payload,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        response.raise_for_status()
        print("response: ", response.content)
        agent_response = ""
        conversation_complete = False
        
        print("🤖 Agent: ", end="", flush=True)
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        if data.get('type') == 'content':
                            content = data.get('content', '')
                            print(content, end="", flush=True)
                            agent_response += content
                        elif data.get('type') == 'complete':
                            print(f"\n\n🎉 Profiling complete! User UUID: {data.get('user_uuid')}")
                            conversation_complete = True
                            break
                        elif data.get('type') == 'error':
                            print(f"\n❌ Error: {data.get('error')}")
                            return None, True
                    except json.JSONDecodeError:
                        pass
        
        print()  # New line after agent response
        return agent_response, conversation_complete
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send message: {e}")
        return None, False

def get_profile(user_uuid):
    """Get the user profile by UUID."""
    try:
        response = requests.get(f"{BASE_URL}{PROFILES_ENDPOINT}/{user_uuid}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get profile: {e}")
        return None

def print_profile(profile):
    """Print the user profile in a formatted way."""
    if not profile:
        print("❌ No profile available.")
        return
    
    print("\n📋 User Profile:")
    print("=" * 50)
    print(f"UUID: {profile.get('uuid')}")
    print(f"Past Favorite Work: {profile.get('past_favorite_work', [])}")
    print(f"Taste Genre: {profile.get('taste_genre', 'Not specified')}")
    print(f"Current Obsession: {profile.get('current_obsession', [])}")
    print(f"State of Mind: {profile.get('state_of_mind', 'Not specified')}")
    print(f"Future Aspirations: {profile.get('future_aspirations', 'Not specified')}")
    print(f"Complete: {profile.get('complete', False)}")
    print(f"Updated: {profile.get('updated_at', 'Unknown')}")
    print("=" * 50)

def list_conversations():
    """List all available conversations."""
    try:
        response = requests.get(f"{BASE_URL}{CONVERSATIONS_ENDPOINT}")
        response.raise_for_status()
        data = response.json()
        conversations = data.get('conversations', [])
        if conversations:
            print(f"\n📋 Available conversations ({len(conversations)}):")
            for i, session_id in enumerate(conversations, 1):
                print(f"  {i}. {session_id}")
        else:
            print("\n📋 No conversations found.")
        return conversations
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to list conversations: {e}")
        return []

def get_conversation(session_id):
    """Get a conversation by session ID."""
    try:
        response = requests.get(f"{BASE_URL}{CONVERSATIONS_ENDPOINT}/{session_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get conversation: {e}")
        return None

def main():
    """
    Main function to run the interactive chat session with the Profiler Agent.
    """
    print("🎭 Profiling Agent Interactive Chat")
    print("=" * 50)
    print("This client connects to the Profiling Agent MCP Server.")
    print("Commands:")
    print("  'quit' - Exit the chat")
    print("  'profile' - Show current profile")
    print("  'list' - List available conversations")
    print("  'load <session_id>' - Load a conversation")
    print("  'new' - Start a new conversation")
    print()

    # Initialize session variables
    session_id = f"notebook-session-{int(time.time())}"
    user_uuid = None
    conversation_history = []
    profiling_complete = False
    
    # Check for existing conversations
    conversations = list_conversations()
    if conversations:
        print("💡 Tip: Use 'load <session_id>' to resume a previous conversation")
    
    # Create a new profile
    print("📝 Creating new user profile...")
    user_uuid = create_profile()
    if not user_uuid:
        print("❌ Failed to create profile. Exiting.")
        return
    
    print(f"✅ Created profile with UUID: {user_uuid}")
    
    # Start the conversation
    print("\n🤖 Starting conversation with the Profiling Agent...")
    agent_response, profiling_complete = send_message(session_id, "Hi", user_uuid)
    
    if agent_response:
        conversation_history.append({"role": "assistant", "content": agent_response})
    
    if profiling_complete:
        print("\n--- Profiling Complete ---")
        print("The agent has finished collecting your information.")
        profile = get_profile(user_uuid)
        if profile:
            print_profile(profile)
        return

    # Main conversation loop
    while not profiling_complete:
        # Get next message from user
        user_input = input("🙂 You: ").strip()
        
        if user_input.lower() == 'quit':
            print("👋 Goodbye!")
            break
        
        elif user_input.lower() == 'profile':
            profile = get_profile(user_uuid)
            if profile:
                print_profile(profile)
            continue
        
        elif user_input.lower() == 'list':
            list_conversations()
            continue
        
        elif user_input.lower().startswith('load '):
            session_id = user_input[5:].strip()
            if session_id:
                conversation = get_conversation(session_id)
                if conversation:
                    print(f"✅ Loaded conversation: {session_id}")
                    user_uuid = conversation.get('user_uuid', user_uuid)
                    conversation_history = conversation.get('messages', [])
                    print(f"   User UUID: {user_uuid}")
                    print(f"   Messages: {len(conversation_history)}")
                else:
                    print(f"❌ Conversation not found: {session_id}")
            else:
                print("❌ Please provide a session ID: load <session_id>")
            continue
        
        elif user_input.lower() == 'new':
            session_id = f"notebook-session-{int(time.time())}"
            user_uuid = create_profile()
            conversation_history = []
            print(f"✅ Started new conversation: {session_id}")
            continue
        
        elif not user_input:
            continue
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Send message to agent
        agent_response, profiling_complete = send_message(session_id, user_input, user_uuid)
        
        if agent_response:
            conversation_history.append({"role": "assistant", "content": agent_response})
        
        if profiling_complete:
            print("\n--- Profiling Complete ---")
            print("The agent has finished collecting your information.")
            profile = get_profile(user_uuid)
            if profile:
                print_profile(profile)
            break

if __name__ == "__main__":
    main() 