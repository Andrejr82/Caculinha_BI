"""
Seed Admin User Script
Creates initial admin user for the system
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import AsyncSessionLocal
from app.config.security import get_password_hash
from app.infrastructure.database.models import User


async def seed_admin():
    """Create admin user"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if admin already exists
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.username == "admin")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print("[ERRO] Admin user already exists")
                return
            
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@agentbi.com",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True,
                allowed_segments='["*"]', # Admin pode ver tudo
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            print("[OK] Admin user created successfully!")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   Email: admin@agentbi.com")
            print(f"   ID: {admin_user.id}")
            print("\n[IMPORTANTE] Change the password after first login!")
            
        except Exception as e:
            print(f"[ERRO] Error creating admin user: {e}")
            await db.rollback()


if __name__ == "__main__":
    print("Seeding admin user...")
    asyncio.run(seed_admin())
