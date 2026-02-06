"""
Script para criar usuário admin no Supabase
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.supabase_client import get_supabase_admin_client

async def create_admin():
    """Create admin user in Supabase"""
    print("=" * 60)
    print("Criando usuário admin no Supabase...")
    print("=" * 60)

    try:
        admin_client = get_supabase_admin_client()

        email = "admin@agentbi.com"
        password = "admin123"
        username = "admin"

        print(f"\n✓ Criando usuário:")
        print(f"  Email: {email}")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"  Role: admin\n")

        # Create user in Supabase Auth using Admin API
        try:
            result = admin_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,  # Auto-confirm email
                "user_metadata": {
                    "role": "admin",
                    "username": username
                }
            })

            if result and result.user:
                user_id = result.user.id
                print(f"✓ Usuário criado com sucesso! ID: {user_id}\n")

                # Create profile in user_profiles table
                print("✓ Criando perfil na tabela user_profiles...")
                supabase = get_supabase_admin_client()

                profile_data = {
                    "id": user_id,
                    "username": username,
                    "role": "admin",
                    "email": email
                }

                profile_result = supabase.table("user_profiles").upsert(profile_data).execute()

                if profile_result:
                    print("✓ Perfil criado com sucesso!\n")
                    print("=" * 60)
                    print("✓ USUÁRIO ADMIN CRIADO COM SUCESSO!")
                    print("=" * 60)
                    print(f"\nCredenciais:")
                    print(f"  Username: {username}")
                    print(f"  Password: {password}")
                    print(f"\nAgora você pode fazer login em: http://localhost:3000")
                    print("=" * 60)
                else:
                    print("⚠ Usuário criado, mas falha ao criar perfil")

            else:
                print("✗ Falha ao criar usuário")

        except Exception as e:
            error_msg = str(e)
            if "already registered" in error_msg.lower() or "duplicate" in error_msg.lower():
                print(f"⚠ Usuário já existe: {email}")
                print("\nTentando atualizar a senha...")

                # Get existing user
                users = admin_client.auth.admin.list_users()
                existing_user = None
                for user in users:
                    if user.email == email:
                        existing_user = user
                        break

                if existing_user:
                    # Update password
                    admin_client.auth.admin.update_user_by_id(
                        existing_user.id,
                        {"password": password}
                    )
                    print(f"✓ Senha atualizada para: {password}")
                    print("\nAgora você pode fazer login!")
                else:
                    print("✗ Não foi possível encontrar o usuário existente")
            else:
                print(f"✗ Erro: {e}")

    except Exception as e:
        print(f"✗ Erro ao conectar com Supabase: {e}")
        print("\nVerifique se:")
        print("1. As variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY estão corretas no .env")
        print("2. O backend está rodando")
        print("3. Você tem acesso à internet")

if __name__ == "__main__":
    asyncio.run(create_admin())
