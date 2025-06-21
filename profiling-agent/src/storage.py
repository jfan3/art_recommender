import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

PROFILES_DIR = "profiles"

def get_profile_path(user_uuid: str) -> str:
    """Constructs the full path for a user's profile JSON file."""
    return os.path.join(PROFILES_DIR, f"{user_uuid}.json")

def read_profile(user_uuid: str) -> Dict[str, Any]:
    """Reads a user's profile from a JSON file."""
    profile_path = get_profile_path(user_uuid)
    if not os.path.exists(profile_path):
        return {"uuid": user_uuid}
    try:
        with open(profile_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"uuid": user_uuid}

def merge_and_save(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges the given data with an existing user profile and saves it.
    Requires 'uuid' to be in the data.
    """
    user_uuid = data.get("uuid")
    if not user_uuid:
        raise ValueError("UUID is required to merge and save profile data.")

    os.makedirs(PROFILES_DIR, exist_ok=True)
    
    # Read existing profile
    profile = read_profile(user_uuid)
    
    # Merge new data into it
    profile.update(data)
    
    # Add timestamp
    profile["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Write back to file
    profile_path = get_profile_path(user_uuid)
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)
        
    return profile
