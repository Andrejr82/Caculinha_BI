"""
Seed Test User Script
Creates a test user for specific segment access
"""

import asyncio
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import AsyncSessionLocal
from app.config.security import get_password_hash
from app.infrastructure.database.models import User
from sqlalchemy import select


async def seed_test_user():
    """Create a test user with specific segment permissions"""
    
    username = "comprador"
    password = "comprador123"
    email = "comprador@agentbi.com"
    allowed_segments = ["INFORMÁTICA"] # Exemplo de segmento do admmat.parquet

    async with AsyncSessionLocal() as db:
        try:
            # Check if user already exists
            result = await db.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"[ERRO] Usuario '{username}' ja existe. Remova-o se quiser recria-lo.")
                return
            
            # Create user
            test_user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                role="user", # Role de usuário comum
                is_active=True,
                allowed_segments=json.dumps(allowed_segments), # Segmentos permitidos
            )
            
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            
            print(f"[OK] Usuario '{username}' criado com sucesso!")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Allowed Segments: {allowed_segments}")
            
        except Exception as e:
            print(f"[ERRO] Erro ao criar usuario '{username}': {e}")
            await db.rollback()


if __name__ == "__main__":
    print("Seeding test user...")
    asyncio.run(seed_test_user())
