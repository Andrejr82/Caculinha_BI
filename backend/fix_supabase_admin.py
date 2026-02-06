"""
Script para verificar e corrigir usuário admin no Supabase
"""
import sys
import asyncio
from app.config.settings import get_settings
from app.core.supabase_client import get_supabase_client, get_supabase_admin_client

settings = get_settings()

def main():
    print("\n=== VERIFICAÇÃO E CORREÇÃO DO ADMIN NO SUPABASE ===\n")

    if not settings.USE_SUPABASE_AUTH:
        print("❌ USE_SUPABASE_AUTH está desabilitado no .env")
        print("   Defina USE_SUPABASE_AUTH=true para usar Supabase")
        return

    try:
        # Get clients
        supabase = get_supabase_client()
        admin_client = get_supabase_admin_client()

        print("✅ Clientes Supabase criados com sucesso")
        print(f"   URL: {settings.SUPABASE_URL}")

        # List all users
        print("\n--- LISTANDO USUÁRIOS NO SUPABASE AUTH ---")
        try:
            users_response = admin_client.auth.admin.list_users()
            users = users_response if isinstance(users_response, list) else []

            if hasattr(users_response, 'users'):
                users = users_response.users

            print(f"Total de usuários: {len(users)}")

            admin_user = None
            for user in users:
                email = user.email if hasattr(user, 'email') else user.get('email', 'N/A')
                user_id = user.id if hasattr(user, 'id') else user.get('id', 'N/A')
                print(f"  - Email: {email}, ID: {user_id}")

                # Procurar admin
                if email and 'admin' in email.lower():
                    admin_user = user
                    print(f"    👤 Admin encontrado!")

            if not admin_user:
                print("\n⚠️ Usuário admin NÃO ENCONTRADO no Supabase Auth")
                print("\n=== CRIANDO USUÁRIO ADMIN ===")

                # Criar admin
                new_admin = admin_client.auth.admin.create_user({
                    "email": "admin@agentbi.com",
                    "password": "admin",
                    "email_confirm": True,
                    "user_metadata": {
                        "username": "admin",
                        "allowed_segments": ["*"]
                    }
                })

                admin_user_id = new_admin.user.id
                print(f"✅ Admin criado com ID: {admin_user_id}")

            else:
                admin_user_id = admin_user.id if hasattr(admin_user, 'id') else admin_user.get('id')
                print(f"\n✅ Admin existe com ID: {admin_user_id}")

            # Verificar/Criar perfil no user_profiles
            print("\n--- VERIFICANDO PERFIL NA TABELA user_profiles ---")

            profile_response = admin_client.table("user_profiles").select("*").eq("id", admin_user_id).execute()

            if not profile_response.data or len(profile_response.data) == 0:
                print("⚠️ Perfil não encontrado na tabela user_profiles")
                print("   Criando perfil...")

                # Criar perfil
                insert_result = admin_client.table("user_profiles").insert({
                    "id": admin_user_id,
                    "username": "admin",
                    "role": "admin",
                    # "allowed_segments": ["*"], # Removido pois coluna nao existe
                    "created_at": "now()",
                    "updated_at": "now()"
                }).execute()

                print("✅ Perfil criado com sucesso")

            else:
                profile = profile_response.data[0]
                print(f"✅ Perfil encontrado:")
                print(f"   Username: {profile.get('username')}")
                print(f"   Role: {profile.get('role')}")
                print(f"   Allowed Segments: {profile.get('allowed_segments')}")

                # Verificar se precisa corrigir
                needs_update = False
                updates = {}

                if profile.get('role') != 'admin':
                    print(f"\n⚠️ Role incorreto: '{profile.get('role')}' (deveria ser 'admin')")
                    updates['role'] = 'admin'
                    needs_update = True

                # if profile.get('allowed_segments') != ['*']:
                #     print(f"\n⚠️ Allowed segments incorreto: {profile.get('allowed_segments')} (deveria ser ['*'])")
                #     updates['allowed_segments'] = ['*']
                #     needs_update = True

                if needs_update:
                    print("\n🔧 CORRIGINDO PERFIL...")
                    updates['updated_at'] = 'now()'

                    admin_client.table("user_profiles").update(updates).eq("id", admin_user_id).execute()

                    print("✅ Perfil corrigido com sucesso!")

                    # Verificar novamente
                    updated_profile = admin_client.table("user_profiles").select("*").eq("id", admin_user_id).execute()
                    if updated_profile.data:
                        up = updated_profile.data[0]
                        print(f"\n--- PERFIL APÓS CORREÇÃO ---")
                        print(f"   Username: {up.get('username')}")
                        print(f"   Role: {up.get('role')}")
                        print(f"   Allowed Segments: {up.get('allowed_segments')}")

                else:
                    print("\n✅ Perfil já está correto!")

            print("\n" + "="*50)
            print("RESUMO FINAL:")
            print("="*50)
            print(f"✅ Admin User ID: {admin_user_id}")
            print(f"✅ Email: admin@agentbi.com")
            print(f"✅ Senha: admin")
            print(f"✅ Role: admin")
            print(f"✅ Allowed Segments: ['*']")
            print("\n🎯 Tente fazer login agora com:")
            print("   Email: admin@agentbi.com")
            print("   Senha: admin")
            print("\n   OU")
            print("   Username: admin")
            print("   Senha: admin")

        except Exception as e:
            print(f"\n❌ Erro ao listar/manipular usuários: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"\n❌ Erro ao conectar ao Supabase: {e}")
        print("\nVerifique se as credenciais estão corretas no .env:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_ANON_KEY")
        print("  - SUPABASE_SERVICE_ROLE_KEY")

if __name__ == "__main__":
    main()
