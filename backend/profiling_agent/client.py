#!/usr/bin/env python3
"""
Simple client for interacting with the Profiling Agent MCP Server.
This script provides a command-line interface to test the chat functionality.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8080"

class ProfilingAgentClient:
    def __init__(self):
        self.session_id = f"cli-session-{int(time.time())}"
        self.user_uuid = None
        self.messages = []
    
    def create_profile(self):
        """Create a new user profile."""
        try:
            response = requests.post(f"{BASE_URL}/profiles")
            if response.status_code == 200:
                data = response.json()
                self.user_uuid = data.get('uuid')
                print(f"✅ Created profile with UUID: {self.user_uuid}")
                return True
            else:
                print(f"❌ Failed to create profile: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure it's running on localhost:8080")
            return False
    
    def list_conversations(self):
        """List all available conversations."""
        try:
            response = requests.get(f"{BASE_URL}/conversations")
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('conversations', [])
                if conversations:
                    print(f"\n📋 Available conversations ({len(conversations)}):")
                    for i, session_id in enumerate(conversations, 1):
                        print(f"  {i}. {session_id}")
                    return conversations
                else:
                    print("\n📋 No conversations found.")
                    return []
            else:
                print(f"❌ Failed to list conversations: {response.text}")
                return []
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server.")
            return []
    
    def load_conversation(self, session_id: str):
        """Load an existing conversation."""
        try:
            response = requests.get(f"{BASE_URL}/conversations/{session_id}")
            if response.status_code == 200:
                conversation = response.json()
                self.session_id = session_id
                self.user_uuid = conversation.get('user_uuid')
                self.messages = conversation.get('messages', [])
                print(f"✅ Loaded conversation: {session_id}")
                print(f"   User UUID: {self.user_uuid}")
                print(f"   Messages: {len(self.messages)}")
                return True
            else:
                print(f"❌ Failed to load conversation: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server.")
            return False
    
    def delete_conversation(self, session_id: str):
        """Delete a conversation."""
        try:
            response = requests.delete(f"{BASE_URL}/conversations/{session_id}")
            if response.status_code == 200:
                print(f"✅ Deleted conversation: {session_id}")
                return True
            else:
                print(f"❌ Failed to delete conversation: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server.")
            return False
    
    def send_message(self, message):
        """Send a message to the profiling agent."""
        if not self.user_uuid:
            if not self.create_profile():
                return False
        
        # Add user message to history
        self.messages.append({"role": "user", "content": message})
        
        payload = {
            "session_id": self.session_id,
            "messages": [{"role": "user", "content": message}],  # Only send the latest message
            "user_uuid": self.user_uuid
        }
        
        try:
            print(f"\n🤖 Agent: ", end="", flush=True)
            
            response = requests.post(
                f"{BASE_URL}/chat",
                json=payload,
                stream=True,
                headers={"Accept": "text/event-stream"}
            )
            
            if response.status_code != 200:
                print(f"❌ Error: {response.text}")
                return False
            
            agent_response = ""
            conversation_complete = False
            
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
                                return False
                        except json.JSONDecodeError:
                            pass
            
            print()  # New line after agent response
            
            # Add agent response to history
            if agent_response:
                self.messages.append({"role": "assistant", "content": agent_response})
            
            return not conversation_complete
            
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure it's running on localhost:8080")
            return False
    
    def get_profile(self):
        """Retrieve the current user profile."""
        if not self.user_uuid:
            print("❌ No profile created yet.")
            return None
        
        try:
            response = requests.get(f"{BASE_URL}/profiles/{self.user_uuid}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get profile: {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server.")
            return None
    
    def print_profile(self):
        """Print the current user profile in a formatted way."""
        profile = self.get_profile()
        if profile:
            print("\n📋 Current Profile:")
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
    
    def print_conversation_history(self):
        """Print the current conversation history."""
        if not self.messages:
            print("\n📝 No conversation history yet.")
            return
        
        print(f"\n💬 Conversation History (Session: {self.session_id}):")
        print("=" * 50)
        for i, message in enumerate(self.messages, 1):
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            if role == 'user':
                print(f"{i}. 🙋 You: {content}")
            elif role == 'assistant':
                print(f"{i}. 🤖 Agent: {content}")
        print("=" * 50)

def main():
    """Main interactive loop."""
    print("🎭 Profiling Agent Client")
    print("=" * 50)
    print("This client helps you interact with the Profiling Agent MCP Server.")
    print("Commands:")
    print("  'quit' - Exit the client")
    print("  'profile' - Show current profile")
    print("  'history' - Show conversation history")
    print("  'list' - List available conversations")
    print("  'load <session_id>' - Load a conversation")
    print("  'delete <session_id>' - Delete a conversation")
    print("  'new' - Start a new conversation")
    print()
    
    client = ProfilingAgentClient()
    
    # Check for existing conversations
    conversations = client.list_conversations()
    if conversations:
        print("💡 Tip: Use 'load <session_id>' to resume a previous conversation")
    
    # Start the conversation
    print("Starting conversation with the Profiling Agent...")
    if not client.send_message("Hi"):
        print("❌ Failed to start conversation. Exiting.")
        return
    
    # Main interaction loop
    while True:
        try:
            user_input = input("\n🙂 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == 'profile':
                client.print_profile()
                continue
            
            elif user_input.lower() == 'history':
                client.print_conversation_history()
                continue
            
            elif user_input.lower() == 'list':
                client.list_conversations()
                continue
            
            elif user_input.lower().startswith('load '):
                session_id = user_input[5:].strip()
                if session_id:
                    client.load_conversation(session_id)
                else:
                    print("❌ Please provide a session ID: load <session_id>")
                continue
            
            elif user_input.lower().startswith('delete '):
                session_id = user_input[7:].strip()
                if session_id:
                    client.delete_conversation(session_id)
                else:
                    print("❌ Please provide a session ID: delete <session_id>")
                continue
            
            elif user_input.lower() == 'new':
                client.session_id = f"cli-session-{int(time.time())}"
                client.user_uuid = None
                client.messages = []
                print(f"✅ Started new conversation: {client.session_id}")
                continue
            
            elif not user_input:
                continue
            
            # Send message to agent
            if not client.send_message(user_input):
                print("❌ Failed to send message. Exiting.")
                break
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main() 