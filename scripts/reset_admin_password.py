"""
Script para resetar senha do usuário admin no Supabase
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.supabase_client import get_supabase_admin_client

async def reset_admin_password():
    """Reset admin password in Supabase"""
    print("=" * 60)
    print("Resetando senha do usuário admin...")
    print("=" * 60)

    try:
        admin_client = get_supabase_admin_client()

        email = "admin@agentbi.com"
        username = "admin"
        new_password = "admin123"

        print(f"\n✓ Buscando usuário admin...")

        # List all users and find admin
        users_response = admin_client.auth.admin.list_users()
        admin_user = None

        for user in users_response:
            if user.email == email:
                admin_user = user
                break

        if not admin_user:
            # Try to find by username in user_metadata
            for user in users_response:
                if user.user_metadata and user.user_metadata.get("username") == username:
                    admin_user = user
                    break

        if admin_user:
            print(f"✓ Usuário encontrado: {admin_user.email} (ID: {admin_user.id})")
            print(f"\n✓ Resetando senha para: {new_password}")

            # Update password
            result = admin_client.auth.admin.update_user_by_id(
                admin_user.id,
                {
                    "password": new_password,
                    "email_confirm": True
                }
            )

            if result:
                print("✓ Senha atualizada com sucesso!")

                # Ensure profile exists
                print("\n✓ Verificando perfil na tabela user_profiles...")
                supabase = get_supabase_admin_client()

                profile_data = {
                    "id": admin_user.id,
                    "username": username,
                    "role": "admin",
                    "email": admin_user.email
                }

                try:
                    profile_result = supabase.table("user_profiles").upsert(profile_data).execute()
                    print("✓ Perfil verificado/atualizado!")
                except Exception as e:
                    print(f"⚠ Aviso ao verificar perfil: {e}")

                print("\n" + "=" * 60)
                print("✓ SENHA RESETADA COM SUCESSO!")
                print("=" * 60)
                print(f"\nCredenciais atualizadas:")
                print(f"  Username: {username}")
                print(f"  Email: {email}")
                print(f"  Password: {new_password}")
                print(f"\nAgora você pode fazer login em: http://localhost:3000")
                print("=" * 60)
            else:
                print("✗ Falha ao atualizar senha")
        else:
            print(f"✗ Usuário admin não encontrado")
            print(f"\nUsuários disponíveis:")
            for user in users_response[:5]:  # Show first 5 users
                print(f"  - {user.email} (ID: {user.id})")

    except Exception as e:
        print(f"\n✗ Erro: {e}")
        print("\nVerifique se:")
        print("1. O arquivo .env tem SUPABASE_SERVICE_ROLE_KEY correto")
        print("2. O backend está rodando")
        print("3. Você tem conexão com a internet")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
