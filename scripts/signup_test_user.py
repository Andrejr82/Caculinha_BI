"""
Sign up a test user in Supabase using public signup API
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.supabase_client import get_supabase_client

def signup_test_user():
    """Sign up a test user using public Supabase API"""
    try:
        print("Signing up test user in Supabase...")

        supabase = get_supabase_client()

        # Use sign_up instead of admin API
        # Note: Email confirmation might be required based on Supabase project settings
        response = supabase.auth.sign_up({
            "email": "admin@agentbi.com",
            "password": "admin123",
            "options": {
                "email_redirect_to": None,
                "data": {
                    "username": "admin",
                    "role": "admin",
                    "full_name": "Administrator"
                }
            }
        })

        if response.user:
            print("User created successfully!")
            print(f"   Email: admin@agentbi.com")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   User ID: {response.user.id}")
            print("\nYou can now login with:")
            print("   Username: admin")
            print("   Password: admin123")

            # Create profile in user_profiles table
            try:
                profile_data = {
                    "id": str(response.user.id),
                    "username": "admin",
                    "role": "admin",
                    "full_name": "Administrator"
                }
                supabase.table("user_profiles").insert(profile_data).execute()
                print("\n   Profile created in user_profiles table")
            except Exception as e:
                print(f"\n   Warning: Could not create profile: {e}")
        else:
            print("Failed: No user returned from signup")

    except Exception as e:
        print(f"Failed to sign up user: {e}")
        sys.exit(1)

if __name__ == "__main__":
    signup_test_user()
