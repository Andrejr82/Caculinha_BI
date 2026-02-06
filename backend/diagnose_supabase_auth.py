"""
Diagnostico Completo de Autenticacao Supabase
Testa login com admin@agentbi.com e identifica problemas
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import json

# Carrega variaveis de ambiente
backend_dir = Path(__file__).parent
load_dotenv(backend_dir / ".env")

print("="*80)
print("DIAGNOSTICO COMPLETO - AUTENTICACAO SUPABASE")
print("="*80)
print()

# Configuracoes
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
USE_SUPABASE_AUTH = os.getenv("USE_SUPABASE_AUTH", "false").lower() == "true"

# Credenciais de teste
TEST_EMAIL = "admin@agentbi.com"
TEST_PASSWORD = "admin123"
TEST_USERNAME = "admin"

print("1. CONFIGURACAO DO .ENV")
print("-" * 80)
print(f"USE_SUPABASE_AUTH: {USE_SUPABASE_AUTH}")
print(f"SUPABASE_URL: {SUPABASE_URL if SUPABASE_URL else '[NAO CONFIGURADO]'}")
print(f"SUPABASE_ANON_KEY: {'[CONFIGURADO]' if SUPABASE_ANON_KEY else '[NAO CONFIGURADO]'}")
print(f"SUPABASE_SERVICE_KEY: {'[CONFIGURADO]' if SUPABASE_SERVICE_KEY else '[NAO CONFIGURADO]'}")
print()

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("[ERRO] Supabase nao esta configurado no .env!")
    print()
    print("Configure as seguintes variaveis:")
    print("  SUPABASE_URL=https://seu-projeto.supabase.co")
    print("  SUPABASE_ANON_KEY=sua-chave-anon")
    print("  USE_SUPABASE_AUTH=true")
    sys.exit(1)

# Importa Supabase
try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
    print("[OK] Biblioteca supabase instalada")
except ImportError as e:
    print(f"[ERRO] Biblioteca supabase nao instalada: {e}")
    print("Execute: pip install supabase")
    sys.exit(1)

print()
print("2. TESTE DE CONEXAO COM SUPABASE")
print("-" * 80)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("[OK] Cliente Supabase criado com sucesso")
except Exception as e:
    print(f"[ERRO] Falha ao criar cliente Supabase: {e}")
    sys.exit(1)

print()
print("3. VERIFICAR SE USUARIO EXISTE NO SUPABASE")
print("-" * 80)

# Tenta buscar usuario na tabela user_profiles
try:
    profile_response = supabase.table("user_profiles").select("*").eq("username", TEST_USERNAME).execute()
    
    if profile_response.data and len(profile_response.data) > 0:
        print(f"[OK] Usuario '{TEST_USERNAME}' encontrado na tabela user_profiles")
        profile = profile_response.data[0]
        print(f"     ID: {profile.get('id')}")
        print(f"     Username: {profile.get('username')}")
        print(f"     Role: {profile.get('role')}")
        print(f"     Created: {profile.get('created_at')}")
        user_id_from_profile = profile.get('id')
    else:
        print(f"[AVISO] Usuario '{TEST_USERNAME}' NAO encontrado na tabela user_profiles")
        print("        O usuario pode nao existir ou a tabela nao esta configurada")
        user_id_from_profile = None
except Exception as e:
    print(f"[ERRO] Falha ao buscar user_profiles: {e}")
    print(f"       Detalhes: {type(e).__name__}")
    user_id_from_profile = None

print()
print("4. TESTE DE AUTENTICACAO COM SUPABASE AUTH")
print("-" * 80)
print(f"Tentando login com:")
print(f"  Email: {TEST_EMAIL}")
print(f"  Senha: {TEST_PASSWORD}")
print()

try:
    response = supabase.auth.sign_in_with_password({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response and response.session and response.session.user:
        user = response.session.user
        print("[OK] AUTENTICACAO BEM-SUCEDIDA!")
        print()
        print("Informacoes do usuario autenticado:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Email confirmado: {user.email_confirmed_at is not None}")
        print(f"  Criado em: {user.created_at}")
        print(f"  Ultimo login: {user.last_sign_in_at}")
        
        if user.user_metadata:
            print(f"  Metadata: {json.dumps(user.user_metadata, indent=4)}")
        
        print()
        print("Token de acesso:")
        print(f"  {response.session.access_token[:50]}...")
        
        # Verifica se o ID bate com o profile
        if user_id_from_profile:
            if str(user.id) == str(user_id_from_profile):
                print()
                print("[OK] ID do usuario autenticado corresponde ao user_profiles")
            else:
                print()
                print(f"[AVISO] ID do usuario autenticado ({user.id}) NAO corresponde ao user_profiles ({user_id_from_profile})")
        
    else:
        print("[ERRO] Autenticacao falhou - resposta vazia")
        print(f"       Response: {response}")
        
except Exception as e:
    print(f"[ERRO] FALHA NA AUTENTICACAO!")
    print(f"       Tipo: {type(e).__name__}")
    print(f"       Mensagem: {str(e)}")
    print()
    
    # Analisa o erro especifico
    error_msg = str(e).lower()
    
    if "invalid login credentials" in error_msg or "invalid" in error_msg:
        print("CAUSA PROVAVEL: Credenciais invalidas")
        print()
        print("Possiveis razoes:")
        print("  1. Senha incorreta")
        print("  2. Usuario nao existe no Supabase Auth")
        print("  3. Email nao confirmado (se confirmacao estiver habilitada)")
        print()
        print("SOLUCOES:")
        print("  A) Criar usuario no Supabase:")
        print("     - Va para: https://supabase.com/dashboard")
        print("     - Authentication > Users > Add User")
        print("     - Email: admin@agentbi.com")
        print("     - Password: admin123")
        print("     - Auto Confirm User: SIM")
        print()
        print("  B) Resetar senha do usuario existente")
        print()
        print("  C) Usar autenticacao Parquet (fallback):")
        print("     USE_SUPABASE_AUTH=false")
        
    elif "network" in error_msg or "connection" in error_msg:
        print("CAUSA PROVAVEL: Problema de rede/conexao")
        print()
        print("SOLUCOES:")
        print("  - Verifique sua conexao com internet")
        print("  - Verifique se a URL do Supabase esta correta")
        print("  - Verifique se o projeto Supabase esta ativo")
        
    elif "api key" in error_msg or "unauthorized" in error_msg:
        print("CAUSA PROVAVEL: Problema com API Key")
        print()
        print("SOLUCOES:")
        print("  - Verifique se SUPABASE_ANON_KEY esta correto")
        print("  - Regenere a chave no dashboard do Supabase")

print()
print("5. VERIFICAR USUARIOS EXISTENTES NO SUPABASE AUTH (se tiver service key)")
print("-" * 80)

if SUPABASE_SERVICE_KEY:
    try:
        # Cria cliente admin
        admin_client = create_client(
            SUPABASE_URL,
            SUPABASE_SERVICE_KEY,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False
            )
        )
        
        # Lista usuarios (limitado a 10)
        users_response = admin_client.auth.admin.list_users()
        
        if users_response:
            print(f"[OK] Encontrados {len(users_response)} usuario(s) no Supabase Auth:")
            print()
            for i, user in enumerate(users_response, 1):
                print(f"{i}. Email: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Confirmado: {user.email_confirmed_at is not None}")
                print(f"   Criado: {user.created_at}")
                print()
        else:
            print("[AVISO] Nenhum usuario encontrado no Supabase Auth")
            
    except Exception as e:
        print(f"[ERRO] Falha ao listar usuarios: {e}")
        print("       Service key pode estar incorreta ou sem permissoes")
else:
    print("[INFO] SUPABASE_SERVICE_ROLE_KEY nao configurado")
    print("       Nao e possivel listar usuarios existentes")

print()
print("6. TESTE DE AUTENTICACAO VIA CODIGO DA APLICACAO")
print("-" * 80)

# Testa usando o AuthService da aplicacao
try:
    sys.path.insert(0, str(backend_dir))
    from app.core.auth_service import auth_service
    
    async def test_app_auth():
        # Testa com username
        print(f"Testando autenticacao com username: {TEST_USERNAME}")
        result = await auth_service.authenticate_user(TEST_USERNAME, TEST_PASSWORD)
        
        if result:
            print("[OK] Autenticacao via AuthService bem-sucedida!")
            print(f"     User ID: {result.get('id')}")
            print(f"     Username: {result.get('username')}")
            print(f"     Email: {result.get('email')}")
            print(f"     Role: {result.get('role')}")
            print(f"     Allowed Segments: {result.get('allowed_segments')}")
        else:
            print("[ERRO] Autenticacao via AuthService falhou")
            print("       Verifique os logs para mais detalhes")
        
        print()
        
        # Testa com email
        print(f"Testando autenticacao com email: {TEST_EMAIL}")
        result2 = await auth_service.authenticate_user(TEST_EMAIL, TEST_PASSWORD)
        
        if result2:
            print("[OK] Autenticacao via AuthService bem-sucedida!")
            print(f"     User ID: {result2.get('id')}")
            print(f"     Username: {result2.get('username')}")
            print(f"     Email: {result2.get('email')}")
            print(f"     Role: {result2.get('role')}")
            print(f"     Allowed Segments: {result2.get('allowed_segments')}")
        else:
            print("[ERRO] Autenticacao via AuthService falhou")
    
    asyncio.run(test_app_auth())
    
except Exception as e:
    print(f"[ERRO] Falha ao testar AuthService: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("FIM DO DIAGNOSTICO")
print("="*80)
print()
print("RESUMO E RECOMENDACOES:")
print()
print("1. Se o usuario NAO existe no Supabase Auth:")
print("   - Crie manualmente no dashboard do Supabase")
print("   - Ou use autenticacao Parquet (USE_SUPABASE_AUTH=false)")
print()
print("2. Se o usuario existe mas a senha esta incorreta:")
print("   - Resete a senha no dashboard do Supabase")
print("   - Ou atualize a senha no codigo")
print()
print("3. Se quiser usar apenas Parquet (RECOMENDADO para desenvolvimento):")
print("   - Edite backend/.env:")
print("   - USE_SUPABASE_AUTH=false")
print("   - O sistema ira usar o arquivo users.parquet automaticamente")
print()
