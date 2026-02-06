"""
Supabase Client Configuration
Singleton instance for Supabase authentication and database access
"""

from supabase import create_client, Client
from app.config.settings import get_settings

settings = get_settings()

# Singleton Supabase clients
_supabase_client: Client | None = None
_supabase_admin_client: Client | None = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance (using anon key for regular operations)"""
    global _supabase_client

    # Only create client if Supabase auth is enabled
    if not settings.USE_SUPABASE_AUTH:
        raise ValueError(
            "Supabase authentication is disabled. "
            "Set USE_SUPABASE_AUTH=true in .env to enable"
        )

    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError(
                "Supabase credentials not configured. "
                "Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env"
            )

        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )

    return _supabase_client


def get_supabase_admin_client() -> Client:
    """
    Get or create Supabase ADMIN client (using service_role key).
    This client has elevated privileges and should ONLY be used for admin operations
    like creating/deleting users.
    """
    global _supabase_admin_client

    if not settings.USE_SUPABASE_AUTH:
        raise ValueError(
            "Supabase authentication is disabled. "
            "Set USE_SUPABASE_AUTH=true in .env to enable"
        )

    if _supabase_admin_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "Supabase admin credentials not configured. "
                "Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env"
            )

        _supabase_admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )

    return _supabase_admin_client


# Convenience exports
supabase = get_supabase_client
supabase_admin = get_supabase_admin_client
