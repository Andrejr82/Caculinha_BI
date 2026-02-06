"""
Create a test user in Supabase for authentication testing
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.supabase_user_service import supabase_user_service

def create_test_user():
    """Create a test admin user in Supabase"""
    try:
        print("Creating test user in Supabase...")

        user = supabase_user_service.create_user(
            email="admin@agentbi.com",
            password="admin123",
            username="admin",
            role="admin",
            full_name="Administrator"
        )

        print(f"✅ User created successfully!")
        print(f"   Email: {user['email']}")
        print(f"   Username: {user['username']}")
        print(f"   Role: {user['role']}")
        print(f"   ID: {user['id']}")
        print("\nYou can now login with:")
        print("   Username: admin")
        print("   Password: admin123")

    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_test_user()
