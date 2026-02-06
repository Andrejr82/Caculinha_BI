"""
Script para verificar se o usuário user@agentbi.com existe no Supabase
"""
import asyncio
from app.config.settings import get_settings
from app.core.supabase_client import get_supabase_client

settings = get_settings()

async def check_user():
    print("=" * 80)
    print("VERIFICANDO USUÁRIO: user@agentbi.com")
    print("=" * 80)
    
    try:
        supabase = get_supabase_client()
        print("\n✅ Cliente Supabase conectado")
        
        # Verificar na tabela user_profiles
        print("\n1. Verificando tabela user_profiles...")
        profile_resp = supabase.table("user_profiles").select("*").eq("email", "user@agentbi.com").execute()
        
        if profile_resp.data:
            print(f"✅ Usuário encontrado na tabela user_profiles:")
            for key, value in profile_resp.data[0].items():
                print(f"   {key}: {value}")
        else:
            print("❌ Usuário NÃO encontrado na tabela user_profiles")
            
        # Tentar autenticar
        print("\n2. Testando autenticação com Supabase Auth...")
        print("   Email: user@agentbi.com")
        print("   Senha: user123 (tentativa)")
        
        try:
            from supabase import AuthApiError
            response = supabase.auth.sign_in_with_password({
                "email": "user@agentbi.com",
                "password": "user123"
            })
            
            if response and response.session and response.session.user:
                print("✅ Autenticação bem-sucedida!")
                user = response.session.user
                print(f"   ID: {user.id}")
                print(f"   Email: {user.email}")
                print(f"   Metadata: {user.user_metadata}")
            else:
                print("❌ Autenticação falhou - sem sessão retornada")
                
        except AuthApiError as e:
            print(f"❌ Erro de autenticação: {e}")
            print("   Possíveis causas:")
            print("   - Senha incorreta")
            print("   - Usuário não existe no Supabase Auth")
            print("   - Email não confirmado")
            
        # Verificar todos os perfis existentes
        print("\n3. Listando todos os perfis existentes...")
        all_profiles = supabase.table("user_profiles").select("id, email, username, role").execute()
        
        if all_profiles.data:
            print(f"✅ Encontrados {len(all_profiles.data)} perfis:")
            for profile in all_profiles.data:
                print(f"   - {profile.get('email', 'N/A')} | {profile.get('username', 'N/A')} | {profile.get('role', 'N/A')}")
        else:
            print("⚠️  Nenhum perfil encontrado na tabela user_profiles")
            
    except Exception as e:
        print(f"❌ Erro ao verificar usuário: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("RECOMENDAÇÕES:")
    print("=" * 80)
    print("\nSe o usuário NÃO existe no Supabase Auth:")
    print("  1. Crie o usuário no dashboard do Supabase (Authentication > Users)")
    print("  2. Use email: user@agentbi.com")
    print("  3. Defina uma senha")
    print("  4. Confirme o email")
    print("\nSe o usuário existe mas não tem perfil:")
    print("  Execute: python create_user_profile.py")
    print("\nSe preferir usar autenticação local (Parquet):")
    print("  Edite backend/.env e defina: USE_SUPABASE_AUTH=false")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(check_user())
