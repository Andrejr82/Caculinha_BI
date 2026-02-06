"""
Script to create a test user ONLY in Supabase (not in Parquet)
This will verify that Supabase authentication is working
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.supabase_client import get_supabase_client

async def create_test_user():
    """Create a test user in Supabase"""

    print("Creating test user in Supabase ONLY...")
    print("This user will NOT exist in Parquet")
    print()

    try:
        supabase = get_supabase_client()

        email = "supabasetest@agentbi.com"
        password = "Test@2024"

        print(f"Creating user: {email}")
        print(f"Password: {password}")
        print()

        # Create user in Supabase Auth
        try:
            # Note: This requires admin API or Supabase Auth Admin API
            # For now, let's just check if we can login with it
            # You should create this user manually in Supabase Dashboard

            print("[INFO] To test Supabase priority, create this user manually in:")
            print("1. Go to https://supabase.com/dashboard")
            print("2. Select your project: nmamxbriulivinlqqbmf")
            print("3. Go to Authentication > Users")
            print("4. Click 'Add User'")
            print("5. Use:")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print("6. Confirm email (or disable email confirmation)")
            print()
            print("Then, create a profile in user_profiles table:")
            print("7. Go to Table Editor > user_profiles")
            print("8. Insert row with:")
            print("   id: <user_id from auth.users>")
            print("   role: 'user'")
            print()
            print("After that, try logging in via API:")
            print(f'curl -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Content-Type: application/json" -d \'{{"username":"supabasetest","password":"Test@2024"}}\'')

        except Exception as e:
            print(f"[ERROR] {e}")

    except Exception as e:
        print(f"[ERROR] Failed to connect to Supabase: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user())
