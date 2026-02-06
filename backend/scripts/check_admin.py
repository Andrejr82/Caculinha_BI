"""Verificar se usuário admin existe"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import AsyncSessionLocal
from app.infrastructure.database.models import User
from sqlalchemy import select

async def check_admin():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.username == "admin")
            )
            admin = result.scalar_one_or_none()
            
            if admin:
                print("✅ Usuário admin EXISTE no banco de dados")
                print(f"\nDetalhes:")
                print(f"  ID: {admin.id}")
                print(f"  Username: {admin.username}")
                print(f"  Email: {admin.email}")
                print(f"  Role: {admin.role}")
                print(f"  Ativo: {admin.is_active}")
                print(f"  Criado em: {admin.created_at}")
                
                if not admin.is_active:
                    print("\n⚠️  PROBLEMA: Usuário está INATIVO!")
                    print("   Execute no SQL Server:")
                    print("   UPDATE users SET is_active = 1 WHERE username = 'admin';")
                else:
                    print("\n✅ Usuário está ATIVO")
                    
            else:
                print("❌ Usuário admin NÃO EXISTE no banco de dados")
                print("\n📝 Solução:")
                print("   Execute: python scripts\\seed_admin.py")
                
    except Exception as e:
        print(f"❌ Erro ao verificar admin: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_admin())
