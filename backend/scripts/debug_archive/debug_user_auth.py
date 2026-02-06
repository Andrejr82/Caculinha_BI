"""
Script para diagnosticar o problema de autenticacao do user@agentbi.com
"""
import os
import sys
from dotenv import load_dotenv

# Force load .env
load_dotenv(override=True)

# Verify environment
print("=" * 80)
print("DIAGNOSTICO DE AUTENTICACAO - user@agentbi.com")
print("=" * 80)

print("\n1. Verificando configuracao do ambiente...")
print(f"   SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NAO DEFINIDO')[:50]}...")
print(f"   SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY', 'NAO DEFINIDO')[:30]}...")
print(f"   USE_SUPABASE_AUTH: {os.getenv('USE_SUPABASE_AUTH', 'NAO DEFINIDO')}")

# Import supabase
try:
    from supabase import create_client, Client
    print("   [OK] supabase-py importado com sucesso")
except ImportError as e:
    print(f"   [ERRO] Erro ao importar supabase: {e}")
    sys.exit(1)

# Connect
url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_ANON_KEY")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not anon_key:
    print("[ERRO] SUPABASE_URL ou SUPABASE_ANON_KEY nao definidos")
    sys.exit(1)

supabase: Client = create_client(url, anon_key)
print("   [OK] Cliente Supabase conectado")

# Test Variables
TEST_EMAIL = "user@agentbi.com"
TEST_PASSWORD = "user123"

print(f"\n2. Testando autenticacao para: {TEST_EMAIL}")
print(f"   Senha de teste: {TEST_PASSWORD}")

try:
    response = supabase.auth.sign_in_with_password({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response and response.session:
        print("\n   [OK] LOGIN BEM-SUCEDIDO!")
        print(f"   User ID: {response.session.user.id}")
        print(f"   Email: {response.session.user.email}")
        print(f"   Email Confirmed: {response.session.user.email_confirmed_at}")
        print(f"   Metadata: {response.session.user.user_metadata}")
    else:
        print("   [ERRO] Login falhou - sem sessao retornada")
        
except Exception as e:
    error_str = str(e)
    print(f"\n   [ERRO] ERRO DE AUTENTICACAO: {e}")
    
    if "Invalid login credentials" in error_str:
        print("\n   [!] DIAGNOSTICO: Credenciais invalidas")
        print("   Possiveis causas:")
        print("   1. Email nao existe no Supabase Auth")
        print("   2. Senha incorreta")
        print("   3. Usuario nao confirmou email")

# Check user_profiles table
print("\n3. Verificando tabela user_profiles...")
try:
    profiles = supabase.table("user_profiles").select("*").eq("email", TEST_EMAIL).execute()
    
    if profiles.data:
        print(f"   [OK] Encontrado no user_profiles:")
        for key, value in profiles.data[0].items():
            print(f"      {key}: {value}")
    else:
        print(f"   [ERRO] Usuario NAO encontrado na tabela user_profiles")
        print("   SOLUCAO: Precisa criar o perfil apos o usuario existir no Auth")
except Exception as e:
    print(f"   [ERRO] Erro ao consultar user_profiles: {e}")

# List ALL users in user_profiles
print("\n4. Listando TODOS os perfis existentes...")
try:
    all_profiles = supabase.table("user_profiles").select("id, email, username, role").execute()
    if all_profiles.data:
        print(f"   Encontrados {len(all_profiles.data)} perfis:")
        for p in all_profiles.data:
            print(f"   - {p.get('email', 'N/A')} | {p.get('username', 'N/A')} | role={p.get('role', 'N/A')}")
    else:
        print("   [!] Nenhum perfil encontrado!")
except Exception as e:
    print(f"   [ERRO] Erro: {e}")

# Check if user exists in Auth using service role (admin operation)
print("\n5. Verificando Auth usando Service Role...")
if service_key:
    try:
        supabase_admin: Client = create_client(url, service_key)
        
        # List users (admin only)
        users_response = supabase_admin.auth.admin.list_users()
        
        found = False
        if users_response:
            print(f"   Total de usuarios no Auth: {len(users_response)}")
            for u in users_response:
                if hasattr(u, 'email') and u.email == TEST_EMAIL:
                    found = True
                    print(f"\n   [OK] Usuario EXISTE no Supabase Auth:")
                    print(f"      ID: {u.id}")
                    print(f"      Email: {u.email}")
                    print(f"      Confirmed: {u.email_confirmed_at}")
                    print(f"      Created: {u.created_at}")
                    break
            
            if not found:
                print(f"\n   [ERRO] Usuario {TEST_EMAIL} NAO EXISTE no Supabase Auth")
                print("\n   SOLUCAO REQUERIDA:")
                print("   1. Va para o dashboard do Supabase")
                print("   2. Authentication > Users")
                print("   3. Clique em 'Add user' > 'Create new user'")
                print(f"   4. Email: {TEST_EMAIL}")
                print("   5. Password: (defina uma senha)")
                print("   6. Marque 'Auto Confirm User'")
                
    except Exception as e:
        print(f"   [ERRO] Erro ao usar service role: {e}")
else:
    print("   [!] SUPABASE_SERVICE_ROLE_KEY nao definido - nao e possivel verificar Auth admin")

print("\n" + "=" * 80)
print("RESUMO:")
print("=" * 80)
