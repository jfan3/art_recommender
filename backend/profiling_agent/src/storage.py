import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
from backend.db.supabase_client import upsert_user_profile
import requests

class ConversationStorage:
    """Handles local JSON storage for conversation history."""
    
    def __init__(self, conversations_dir: str = "conversations"):
        if conversations_dir is None:
            conversations_dir = ""
        self.conversations_dir = Path(conversations_dir)
        self.conversations_dir.mkdir(exist_ok=True)
    
    def save_conversation(self, session_id: str, messages: List[Dict[str, str]], user_uuid: str = None) -> bool:
        """Save conversation history to JSON file."""
        if not session_id:
            return False
        conversation = {
            "session_id": session_id,
            "user_uuid": user_uuid,
            "messages": messages,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        try:
            conversation_path = self.conversations_dir / f"{session_id}.json"
            with open(conversation_path, 'w') as f:
                json.dump(conversation, f, indent=2)
            return True
        except (IOError, TypeError):
            return False
    
    def load_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation history from JSON file."""
        if not session_id:
            return None
        conversation_path = self.conversations_dir / f"{session_id}.json"
        if not conversation_path.exists():
            return None
        try:
            with open(conversation_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get just the messages from a conversation."""
        if not session_id:
            return []
        conversation = self.load_conversation(session_id)
        if conversation:
            return conversation.get("messages", [])
        return []
    
    def append_message(self, session_id: str, message: Dict[str, str], user_uuid: str = None) -> bool:
        """Append a new message to existing conversation or create new one."""
        if not session_id:
            return False
        conversation = self.load_conversation(session_id)
        if conversation:
            # Update existing conversation
            conversation["messages"].append(message)
            conversation["updated_at"] = datetime.utcnow().isoformat() + "Z"
            if user_uuid:
                conversation["user_uuid"] = user_uuid
        else:
            # Create new conversation
            conversation = {
                "session_id": session_id,
                "user_uuid": user_uuid,
                "messages": [message],
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
        return self.save_conversation(session_id, conversation["messages"], conversation["user_uuid"])
    
    def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation file."""
        if not session_id:
            return False
        conversation_path = self.conversations_dir / f"{session_id}.json"
        if conversation_path.exists():
            try:
                conversation_path.unlink()
                return True
            except IOError:
                return False
        return False
    
    def list_conversations(self) -> List[str]:
        """List all session IDs."""
        sessions = []
        for file_path in self.conversations_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    conversation = json.load(f)
                    sessions.append(conversation["session_id"])
            except (json.JSONDecodeError, IOError):
                continue
        return sessions
    
    def get_conversations_by_user(self, user_uuid: str) -> List[Dict[str, Any]]:
        """Get all conversations for a specific user."""
        conversations = []
        for file_path in self.conversations_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    conversation = json.load(f)
                    if conversation.get("user_uuid") == user_uuid:
                        conversations.append(conversation)
            except (json.JSONDecodeError, IOError):
                continue
        return conversations

class ProfileStorage:
    """Handles local JSON storage for user profiles."""
    
    def __init__(self, profiles_dir: str = "profiles"):
        if profiles_dir is None:
            profiles_dir = ""
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
    
    def _generate_profile_filename(self, user_uuid: str) -> str:
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        short_hash = hashlib.sha256(user_uuid.encode()).hexdigest()[:8]
        return f"{timestamp}_{short_hash}.json"

    def create_profile(self, user_uuid: str = None) -> str:
        """Create a new profile with a UUID and return the UUID."""
        if user_uuid is None:
            user_uuid = str(uuid.uuid4())
        filename = self._generate_profile_filename(user_uuid)
        profile = {
            "uuid": user_uuid,
            "filename": filename,
            "past_favorite_work": [],
            "taste_genre": "",
            "current_obsession": [],
            "state_of_mind": "",
            "future_aspirations": "",
            "complete": False,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        self._save_profile(profile)
        # --- Supabase logging ---
        upsert_user_profile({k: v for k, v in profile.items() if k != "filename"})
        return user_uuid
    
    def _find_profile_file(self, user_uuid: str) -> Optional[Path]:
        if not user_uuid:
            return None
        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    profile = json.load(f)
                    if profile.get("uuid") == user_uuid:
                        return file_path
            except (json.JSONDecodeError, IOError):
                continue
        return None

    def get_profile(self, user_uuid: str) -> Optional[Dict[str, Any]]:
        """Retrieve a profile by UUID."""
        if not user_uuid:
            return None
        profile_path = self._find_profile_file(user_uuid)
        if not profile_path:
            return None
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def merge_profile(self, user_uuid: str, updates: Dict[str, Any]) -> bool:
        """Merge updates into an existing profile."""
        if not user_uuid:
            return False
        profile = self.get_profile(user_uuid)
        if profile is None:
            return False
        
        # Update fields
        for key, value in updates.items():
            if key in profile and key != "uuid":
                profile[key] = value
        
        # Update timestamp
        profile["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        self._save_profile(profile)
        # --- Supabase logging ---
        upsert_user_profile({k: v for k, v in profile.items() if k != "filename"})
        return True
    
    def is_profile_complete(self, user_uuid: str) -> bool:
        """Check if all required fields are filled."""
        if not user_uuid:
            return False
        profile = self.get_profile(user_uuid)
        if profile is None:
            return False
        
        required_fields = [
            "past_favorite_work",
            "taste_genre", 
            "current_obsession",
            "state_of_mind",
            "future_aspirations"
        ]
        
        for field in required_fields:
            value = profile.get(field)
            if not value or (isinstance(value, list) and len(value) == 0):
                return False
        
        return True
    
    def _save_profile(self, profile: Dict[str, Any]):
        """Save profile to JSON file."""
        if not profile or not profile.get("uuid"):
            return
        filename = profile.get("filename")
        if not filename:
            filename = self._generate_profile_filename(profile["uuid"])
            profile["filename"] = filename
        profile_path = self.profiles_dir / filename
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
    
    def list_profiles(self) -> list:
        """List all profile UUIDs."""
        profiles = []
        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    profile = json.load(f)
                    profiles.append(profile["uuid"])
            except (json.JSONDecodeError, IOError):
                continue
        return profiles

class StorageManager:
    """Combined storage manager for both profiles and conversations."""
    
    def __init__(self, profiles_dir: str = "profiles", conversations_dir: str = "conversations"):
        self.profiles = ProfileStorage(profiles_dir)
        self.conversations = ConversationStorage(conversations_dir)
    
    # Profile methods
    def create_profile(self, user_uuid: str = None) -> str:
        return self.profiles.create_profile(user_uuid)
    
    def get_profile(self, user_uuid: str) -> Optional[Dict[str, Any]]:
        if not user_uuid:
            return None
        return self.profiles.get_profile(user_uuid)
    
    def merge_profile(self, user_uuid: str, updates: Dict[str, Any]) -> bool:
        if not user_uuid:
            return False
        return self.profiles.merge_profile(user_uuid, updates)
    
    def is_profile_complete(self, user_uuid: str) -> bool:
        if not user_uuid:
            return False
        return self.profiles.is_profile_complete(user_uuid)
    
    def list_profiles(self) -> list:
        return self.profiles.list_profiles()
    
    # Conversation methods
    def save_conversation(self, session_id: str, messages: List[Dict[str, str]], user_uuid: str = None) -> bool:
        if not session_id:
            return False
        return self.conversations.save_conversation(session_id, messages, user_uuid)
    
    def load_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not session_id:
            return None
        return self.conversations.load_conversation(session_id)
    
    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        if not session_id:
            return []
        return self.conversations.get_messages(session_id)
    
    def append_message(self, session_id: str, message: Dict[str, str], user_uuid: str = None) -> bool:
        if not session_id:
            return False
        return self.conversations.append_message(session_id, message, user_uuid)
    
    def delete_conversation(self, session_id: str) -> bool:
        if not session_id:
            return False
        return self.conversations.delete_conversation(session_id)
    
    def list_conversations(self) -> List[str]:
        return self.conversations.list_conversations()
    
    def get_conversations_by_user(self, user_uuid: str) -> List[Dict[str, Any]]:
        if not user_uuid:
            return []
        return self.conversations.get_conversations_by_user(user_uuid) 