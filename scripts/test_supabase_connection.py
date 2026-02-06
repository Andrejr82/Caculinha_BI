import asyncio
import os
import sys
from pathlib import Path

# Adicionar diretório backend ao path para importar modulos da app
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.config.settings import settings
from app.core.supabase_user_service import supabase_user_service

async def test_supabase_connection():
    print("🚀 Testando Conexão com Supabase Auth Admin...")
    print(f"URL: {settings.SUPABASE_URL}")
    print(f"Service Role Key Presente: {'Sim' if settings.SUPABASE_SERVICE_ROLE_KEY else 'Não'}")

    try:
        # Tentar listar usuários
        print("\n📋 Listando usuários...")
        users = supabase_user_service.list_users(limit=5)
        print(f"✅ Sucesso! Encontrados {len(users)} usuários.")
        for u in users:
            print(f"   - {u['email']} ({u['role']})")

    except Exception as e:
        print(f"❌ Erro ao listar usuários: {e}")
        return

    # Tentar criar um usuário de teste
    test_email = "supabase_debug_test@example.com"
    try:
        print(f"\n👤 Tentando buscar usuário de teste '{test_email}'...")
        # Lógica simplificada, na verdade list_users não filtra por email diretamente no service wrapper atual aparentemente
        # Vamos tentar criar, se der erro que já existe, tudo bem.
        
        print(f"👤 Tentando criar usuário de teste '{test_email}'...")
        try:
            new_user = supabase_user_service.create_user(
                email=test_email,
                password="Password123!",
                username="supa_debug",
                role="viewer"
            )
            print("✅ Usuário criado com sucesso!")
            print(new_user)
            
            # Limpar (Deletar)
            print("\n🗑️ Limpando usuário de teste...")
            supabase_user_service.delete_user(new_user['id'])
            print("✅ Usuário deletado.")
            
        except Exception as e:
            if "already registered" in str(e) or "already exists" in str(e):
                 print("⚠️ Usuário já existe (Esperado se rodou antes).")
            else:
                print(f"❌ Erro ao criar usuário: {e}")

    except Exception as e:
        print(f"❌ Erro erro geral no teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_supabase_connection())
