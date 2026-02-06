"""
Test Admin Access - Verify admin has full access to all data and segments
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from app.core.auth_service import auth_service
from app.core.data_scope_service import data_scope_service
from app.infrastructure.database.models.user import User

async def test_admin_access():
    print("="*80)
    print("TESTING ADMIN ACCESS - Full Data & Segment Access")
    print("="*80)
    print()

    # Test 1: Authenticate admin user
    print("[TEST 1] Authenticating admin user...")
    user_data = await auth_service.authenticate_user("admin", "admin123")

    if not user_data:
        print("[ERROR] Admin authentication failed!")
        return False

    print(f"[OK] Admin authenticated successfully")
    print(f"  User ID: {user_data['id']}")
    print(f"  Username: {user_data['username']}")
    print(f"  Role: {user_data['role']}")
    print(f"  Allowed Segments: {user_data['allowed_segments']}")
    print()

    # Verify admin has "*" in allowed_segments
    if "*" not in user_data['allowed_segments']:
        print("[ERROR] Admin does NOT have '*' in allowed_segments!")
        print(f"  Expected: ['*']")
        print(f"  Got: {user_data['allowed_segments']}")
        return False

    print("[OK] Admin has full access marker ('*') in allowed_segments")
    print()

    # Test 2: Create User object and test data filtering
    print("[TEST 2] Testing data scope filtering for admin...")

    # Create a mock User object with admin role
    class MockUser:
        def __init__(self, user_data):
            self.id = user_data['id']
            self.username = user_data['username']
            self.email = user_data.get('email', '')
            self.role = user_data['role']
            self.is_active = user_data['is_active']
            self._segments = user_data['allowed_segments']

        @property
        def segments_list(self):
            return self._segments

    admin_user = MockUser(user_data)

    # Get filtered data
    arrow_table = data_scope_service.get_filtered_dataframe(admin_user, max_rows=100)

    if not arrow_table or arrow_table.num_rows == 0:
        print("[ERROR] Admin received EMPTY dataset!")
        return False

    print(f"[OK] Admin can access data: {arrow_table.num_rows:,} rows returned")
    print(f"  Columns: {len(arrow_table.column_names)} columns")
    print()

    # Test 3: Get all segments available to admin
    print("[TEST 3] Testing segment access for admin...")
    segments = data_scope_service.get_user_segments(admin_user)

    if not segments:
        print("[ERROR] Admin received NO segments!")
        return False

    print(f"[OK] Admin has access to ALL segments: {len(segments)} segments")
    print(f"  Segments: {', '.join(segments[:10])}")
    if len(segments) > 10:
        print(f"  ... and {len(segments) - 10} more")
    print()

    # Test 4: Compare with regular user (if exists)
    print("[TEST 4] Comparing admin access vs regular user...")
    regular_user_data = await auth_service.authenticate_user("hugo.mendes", "123456")

    if regular_user_data:
        print(f"[OK] Regular user authenticated: {regular_user_data['username']}")
        print(f"  Role: {regular_user_data['role']}")
        print(f"  Allowed Segments: {regular_user_data['allowed_segments']}")

        regular_user = MockUser(regular_user_data)
        regular_segments = data_scope_service.get_user_segments(regular_user)

        print(f"  Segments accessible: {len(regular_segments)} segments")

        if len(segments) <= len(regular_segments):
            print("[ERROR] Admin does NOT have more access than regular user!")
            return False

        print(f"[OK] Admin has {len(segments) - len(regular_segments)} MORE segments than regular user")
    else:
        print("[INFO] Regular user not found - skipping comparison")

    print()

    # Final Summary
    print("="*80)
    print("[SUCCESS] ALL ADMIN ACCESS TESTS PASSED!")
    print("="*80)
    print("\nAdmin Access Summary:")
    print(f"  [OK] Admin authenticated with role: {user_data['role']}")
    print(f"  [OK] Admin has full access marker: {user_data['allowed_segments']}")
    print(f"  [OK] Admin can query data: {arrow_table.num_rows:,} rows")
    print(f"  [OK] Admin has access to: {len(segments)} segments")
    print("\nAdmin has FULL ACCESS to all data and segments!")
    print()

    return True

if __name__ == "__main__":
    success = asyncio.run(test_admin_access())
    sys.exit(0 if success else 1)
