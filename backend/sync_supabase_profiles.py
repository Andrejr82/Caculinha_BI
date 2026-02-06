"""
Script to sync Supabase profiles for critical users (admin, user).
This ensures they exist in BOTH auth.users and public.user_profiles.
"""
import asyncio
import os
import sys
import json
from pathlib import Path

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from app.config.settings import get_settings
from app.core.supabase_client import get_supabase_client
from supabase import Client, ClientOptions

settings = get_settings()

CRITICAL_USERS = [
    {
        "username": "admin",
        "email": "admin@agentbi.com",
        "password": "admin123", # Default, should be changed
        "role": "admin",
        "allowed_segments": ["*"]
    },
    {
        "username": "user",
        "email": "user@agentbi.com",
        "password": "user123",
        "role": "user",
        # Default user segments (can be adjusted)
        "allowed_segments": ["PAPELARIA", "ARTES", "FESTAS"] 
    }
]

async def sync_profiles():
    print("=" * 80)
    print("SYNC SUPABASE PROFILES")
    print("=" * 80)

    if not settings.USE_SUPABASE_AUTH:
        print("⚠️  USE_SUPABASE_AUTH is False. Skipping sync.")
        return

    try:
        # Use service role key if available for admin tasks
        msg = ""
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            msg = " (WARNING: Using ANON KEY - might fail for admin tasks)"
        
        print(f"Connecting to Supabase... {msg}")
        
        # We need a client with service role for admin actions if possible
        supabase: Client = Client(
            settings.SUPABASE_URL, 
            key,
            options=ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=10
            )
        )

        for user_def in CRITICAL_USERS:
            email = user_def["email"]
            username = user_def["username"]
            print(f"\nProcessing user: {username} ({email})...")

            # 1. Check/Create Auth User
            user_id = None
            try:
                # Try simple sign in first to check existence (if password matches)
                # Or use admin api if available (not exposed in simple client usually)
                # Verify if user exists strictly
                # Since we don't have full admin SDK handy, let's try to sign up. 
                # If it fails, user exists.
                
                print("  - Checks Auth User...")
                try:
                    # Attempt sign up
                    resp = supabase.auth.sign_up({
                        "email": email,
                        "password": user_def["password"],
                        "options": {
                            "data": {
                                "username": username,
                                "role": user_def["role"]
                            }
                        }
                    })
                    if resp.user:
                        user_id = resp.user.id
                        print(f"    ✅ Created new Auth User: {user_id}")
                    elif resp.session and resp.session.user:
                         user_id = resp.session.user.id
                         print(f"    ✅ User already exists (logged in): {user_id}")
                         
                except Exception as e:
                    if "already registered" in str(e) or "User already registered" in str(e):
                        print("    ℹ️  User already registered in Auth.")
                        # We need the ID. Try login to get it.
                        try:
                            login = supabase.auth.sign_in_with_password({
                                "email": email,
                                "password": user_def["password"]
                            })
                            if login.user:
                                user_id = login.user.id
                                print(f"    ✅ Retrieved ID via login: {user_id}")
                        except Exception as login_err:
                            print(f"    ⚠️  Could not log in (wrong password?): {login_err}")
                            # Impossible to get ID without admin key if password changed.
                            # Proceeding to check profile by email if possible
                    else:
                        print(f"    ❌ Error creating user: {e}")

            except Exception as e:
                print(f"  ❌ Auth check failed: {e}")

            # 2. Update Auth Metadata (Best place for permissions without schema changes)
            # Requires service_role key to work for other users
            if user_id:
                try:
                    print("  - Updating Auth Metadata...")
                    # Note: The python client 'auth.update_user' updates the CURRENT user. 
                    # To update OTHERS, we need admin access. 
                    # supabase-py's 'auth.admin' might be available depending on version.
                    
                    metadata = {
                        "username": username,
                        "role": user_def["role"],
                        "allowed_segments": user_def["allowed_segments"]
                    }
                    
                    # Try admin endpoint if available
                    if hasattr(supabase.auth, 'admin'):
                        supabase.auth.admin.update_user_by_id(
                            user_id, 
                            {"user_metadata": metadata}
                        )
                        print(f"    ✅ Auth Metadata updated (via admin).")
                    else:
                        # Fallback: We can't easily update other users' metadata without admin API
                        print(f"    ⚠️  Cannot update metadata (Admin API not available in this client version).")
                        
                except Exception as e:
                    print(f"    ⚠️  Metadata update failed: {e}")

            # 3. Check/Create Profile in `user_profiles` table
            print("  - Syncing user_profiles table...")
            
            try:
                # Check existence
                query = supabase.table("user_profiles").select("*").eq("email", email)
                existing = query.execute()
                
                # Exclude allowed_segments as column might not exist
                profile_data = {
                    "email": email,
                    "username": username,
                    "role": user_def["role"],
                    "is_active": True
                }
                
                # Only add id if we know it
                if user_id:
                    profile_data["id"] = user_id

                if existing.data:
                    # Update
                    print(f"    ℹ️  Profile exists. Updating basic info...")
                    match_col = "id" if user_id else "email"
                    match_val = user_id if user_id else email
                    
                    supabase.table("user_profiles").update(profile_data).eq(match_col, match_val).execute()
                    print(f"    ✅ Profile updated.")
                else:
                    # Insert
                    if not user_id:
                        print("    ❌ Cannot create profile: Missing User ID")
                        continue
                        
                    print(f"    Creating new profile...")
                    supabase.table("user_profiles").insert(profile_data).execute()
                    print(f"    ✅ Profile created.")
                    
            except Exception as e:
                print(f"    ❌ Profile sync failed: {e}")

    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(sync_profiles())
