"""
Script para verificar e corrigir role do admin no Supabase
Garante que admin tenha role='admin' na tabela user_profiles
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carrega variaveis de ambiente
backend_dir = Path(__file__).parent
load_dotenv(backend_dir / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

print("="*70)
print("VERIFICACAO E CORRECAO DO ADMIN NO SUPABASE")
print("="*70)
print()

if not SUPABASE_URL:
    print("[ERRO] SUPABASE_URL nao configurado no .env")
    sys.exit(1)

try:
    from supabase import create_client
    # from supabase.lib.client_options import ClientOptions
except ImportError:
    print("[ERRO] supabase nao instalado. Execute: pip install supabase")
    sys.exit(1)

# Conecta ao Supabase
print(f"[OK] Conectando ao Supabase: {SUPABASE_URL}")

if SUPABASE_SERVICE_KEY:
    # Usar service key para acesso admin
    client = create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_KEY
    )
    print("[OK] Usando Service Role Key (acesso admin)")
else:
    # Usar anon key
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("[AVISO] Usando Anon Key (acesso limitado)")

print()
print("1. VERIFICANDO TABELA user_profiles")
print("-"*70)

# Buscar todos os perfis
try:
    response = client.table("user_profiles").select("*").execute()
    
    if response.data:
        print(f"[OK] Encontrados {len(response.data)} perfis:")
        print()
        
        admin_found = False
        admin_profile = None
        
        for profile in response.data:
            username = profile.get("username", "N/A")
            role = profile.get("role", "N/A")
            user_id = profile.get("id", "N/A")
            
            status = "[ADMIN]" if role == "admin" else "[USER]"
            print(f"  {status} {username} (role={role}, id={user_id})")
            
            if username == "admin":
                admin_found = True
                admin_profile = profile
        
        print()
        
        # Verificar se admin tem role correto
        if admin_found:
            if admin_profile.get("role") == "admin":
                print("[OK] Usuario 'admin' tem role='admin' corretamente!")
            else:
                print(f"[PROBLEMA] Usuario 'admin' tem role='{admin_profile.get('role')}' ao inves de 'admin'")
                print()
                print("Corrigindo...")
                
                # Atualizar role
                update_response = client.table("user_profiles").update({"role": "admin"}).eq("username", "admin").execute()
                
                if update_response.data:
                    print("[OK] Role do admin atualizado para 'admin'!")
                else:
                    print("[ERRO] Falha ao atualizar role do admin")
        else:
            print("[AVISO] Usuario 'admin' nao encontrado na tabela user_profiles")
            print()
            print("Isso pode significar que:")
            print("  1. O usuario nao foi criado no Supabase Auth")
            print("  2. O perfil nao foi criado na tabela user_profiles")
            print()
            print("Execute 'python create_admin_supabase.py' para criar o usuario admin")
    else:
        print("[AVISO] Tabela user_profiles esta vazia")
        print("Execute 'python create_admin_supabase.py' para criar o usuario admin")
        
except Exception as e:
    print(f"[ERRO] Falha ao acessar tabela user_profiles: {e}")
    print()
    print("Possiveis causas:")
    print("  1. Tabela user_profiles nao existe no Supabase")
    print("  2. Permissoes RLS bloqueando acesso")
    print("  3. Service key incorreta")

print()
print("2. VERIFICANDO USUARIOS NO SUPABASE AUTH")
print("-"*70)

if SUPABASE_SERVICE_KEY:
    try:
        users = client.auth.admin.list_users()
        
        print(f"[OK] Encontrados {len(users)} usuarios no Supabase Auth:")
        print()
        
        for user in users:
            email = user.email
            user_id = user.id
            metadata = user.user_metadata or {}
            role_in_metadata = metadata.get("role", "N/A")
            
            print(f"  Email: {email}")
            print(f"  ID: {user_id}")
            print(f"  Role (metadata): {role_in_metadata}")
            print()
            
    except Exception as e:
        print(f"[ERRO] Falha ao listar usuarios: {e}")
else:
    print("[AVISO] Service key nao disponivel - nao e possivel listar usuarios do Auth")

print()
print("="*70)
print("RESUMO")
print("="*70)
print()
print("Para garantir que o admin tenha acesso global:")
print()
print("1. O usuario deve existir no Supabase Auth (email: admin@agentbi.com)")
print("2. Deve haver um perfil na tabela user_profiles com role='admin'")
print("3. O codigo em auth_service.py ja garante allowed_segments=['*'] para admin")
print()
print("Se o problema persistir:")
print("  - Verifique os logs do backend para mensagens de autenticacao")
print("  - Confirme que USE_SUPABASE_AUTH=true no .env")
print("  - Execute 'python create_admin_supabase.py' para recriar o admin")
print()
