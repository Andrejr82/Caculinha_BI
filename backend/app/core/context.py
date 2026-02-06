from contextvars import ContextVar
from typing import Optional, List
from app.infrastructure.database.models import User

# Context variable to hold the current user for the request duration
_current_user_context: ContextVar[Optional[User]] = ContextVar("current_user_context", default=None)

def set_current_user_context(user: User):
    """Set the user for the current request context."""
    _current_user_context.set(user)

def get_current_user_context() -> Optional[User]:
    """Get the user from the current request context."""
    return _current_user_context.get()

def get_current_user_segments() -> List[str]:
    """Get allowed segments for the current user safely."""
    user = get_current_user_context()
    if not user:
        return []
    
    # Admin or full access
    if user.role == "admin" or "*" in user.segments_list:
        return ["*"]
        
    return user.segments_list
