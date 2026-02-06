import json
import os
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, storage_dir: str = "data/sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, session_id: str) -> Path:
        # Security: Validate session_id is a valid UUID to prevent path traversal
        import uuid
        try:
            uuid.UUID(session_id)
        except ValueError:
            # Fallback for legacy IDs: strictly alphanumeric only (no slashes, dots, etc.)
            if not session_id.isalnum():
                 logger.error(f"Invalid session_id format (potential path traversal): '{session_id}' (Len: {len(session_id)}, Type: {type(session_id)})")
                 import sys
                 print(f"[ERROR] [DEBUG] INVALID SESSION ID DETECTED: '{session_id}'", file=sys.stderr)
                 raise ValueError("Invalid session_id format")
        
        return self.storage_dir / f"{session_id}.json"

    def get_history(self, session_id: str, user_id: str) -> List[Dict[str, str]]:
        """Retrieves chat history for a given session ID, verified by user_id."""
        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Security: Verify ownership
                if data.get("user_id") and str(data.get("user_id")) != str(user_id):
                    logger.warning(f"IDOR Attempt: User {user_id} tried to access session {session_id} owned by {data.get('user_id')}")
                    return []
                    
                return data.get("history", [])
        except Exception as e:
            logger.error(f"Error reading session {session_id}: {e}")
            return []

    def add_message(self, session_id: str, role: str, content: str, user_id: str):
        """Adds a message to the session history, ensuring user_id is stored."""
        file_path = self._get_file_path(session_id)
        history = self.get_history(session_id, user_id)
        
        history.append({"role": role, "content": content})
        
        # Limit history length to prevent context window explosion (e.g., last 20 messages)
        if len(history) > 20:
            history = history[-20:]

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "user_id": str(user_id),
                    "history": history
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")

    def clear_session(self, session_id: str):
        """Deletes a session file."""
        file_path = self._get_file_path(session_id)
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error clearing session {session_id}: {e}")
