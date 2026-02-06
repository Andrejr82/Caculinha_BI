"""
Script para criar usuario admin no Supabase
Cria o usuario admin@agentbi.com com senha admin123
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

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("="*80)
    print("ERRO: Configuracao incompleta")
    print("="*80)
    print()
    print("Este script requer:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_SERVICE_ROLE_KEY (service role key, nao anon key!)")
    print()
    print("Configure no arquivo backend/.env")
    print()
    print("Para obter a Service Role Key:")
    print("  1. Va para: https://supabase.com/dashboard")
    print("  2. Selecione seu projeto")
    print("  3. Settings > API")
    print("  4. Copie a 'service_role' key (NAO a 'anon' key)")
    print()
    sys.exit(1)

try:
    from supabase import create_client
    from supabase.lib.client_options import ClientOptions
except ImportError:
    print("Erro: biblioteca supabase nao instalada")
    print("Execute: pip install supabase")
    sys.exit(1)

print("="*80)
print("CRIAR USUARIO ADMIN NO SUPABASE")
print("="*80)
print()

# Configuracoes do usuario admin
ADMIN_EMAIL = "admin@agentbi.com"
ADMIN_PASSWORD = "admin123"
ADMIN_USERNAME = "admin"
ADMIN_ROLE = "admin"

print(f"Conectando ao Supabase: {SUPABASE_URL}")
print()

# Cria cliente admin
try:
    admin_client = create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_KEY
    )
    print("[OK] Cliente admin criado")
except Exception as e:
    print(f"[ERRO] Falha ao criar cliente: {e}")
    sys.exit(1)

print()
print("PASSO 1: Verificar se usuario ja existe")
print("-" * 80)

# Verifica se usuario ja existe
try:
    users = admin_client.auth.admin.list_users()
    existing_user = None
    
    for user in users:
        if user.email == ADMIN_EMAIL:
            existing_user = user
            break
    
    if existing_user:
        print(f"[INFO] Usuario '{ADMIN_EMAIL}' ja existe!")
        print(f"       ID: {existing_user.id}")
        print(f"       Criado em: {existing_user.created_at}")
        print(f"       Email confirmado: {existing_user.email_confirmed_at is not None}")
        print()
        
        # Non-interactive mode: Force delete
        print("Modo nao-interativo: Deletando e recriando usuario...")
        resposta = 's'
        if resposta.lower() == 's':
            print(f"Deletando usuario {existing_user.id}...")
            
            # Tenta deletar perfil primeiro (FK constraint)
            try:
                admin_client.table("user_profiles").delete().eq("id", existing_user.id).execute()
                print("[OK] Perfil deletado da tabela user_profiles")
            except Exception as e:
                print(f"[AVISO] Erro ao deletar perfil (pode nao existir): {e}")
            
            admin_client.auth.admin.delete_user(existing_user.id)
            print("[OK] Usuario deletado")
            existing_user = None
        else:
            print("[INFO] Mantendo usuario existente")
            print()
            print("Se voce esqueceu a senha, voce pode:")
            print("  1. Deletar e recriar o usuario executando este script novamente")
            print("  2. Resetar a senha no dashboard do Supabase")
            print("  3. Usar autenticacao Parquet (USE_SUPABASE_AUTH=false)")
            sys.exit(0)
            
except Exception as e:
    print(f"[ERRO] Falha ao verificar usuarios: {e}")
    sys.exit(1)

if not existing_user:
    print()
    print("PASSO 2: Criar usuario no Supabase Auth")
    print("-" * 80)
    
    try:
        # Cria usuario
        new_user = admin_client.auth.admin.create_user({
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "email_confirm": True,  # Auto-confirma o email
            "user_metadata": {
                "role": ADMIN_ROLE,
                "username": ADMIN_USERNAME
            }
        })
        
        print(f"[OK] Usuario criado com sucesso!")
        print(f"     ID: {new_user.user.id}")
        print(f"     Email: {new_user.user.email}")
        print()
        
        user_id = new_user.user.id
        
    except Exception as e:
        print(f"[ERRO] Falha ao criar usuario: {e}")
        sys.exit(1)
    
    print()
    print("PASSO 3: Criar perfil na tabela user_profiles")
    print("-" * 80)
    
    try:
        # Verifica se a tabela user_profiles existe
        profile_data = {
            "id": user_id,
            "username": ADMIN_USERNAME,
            "role": ADMIN_ROLE,
            "is_active": True
        }
        
        # Tenta inserir
        result = admin_client.table("user_profiles").insert(profile_data).execute()
        
        print(f"[OK] Perfil criado na tabela user_profiles")
        print(f"     Username: {ADMIN_USERNAME}")
        print(f"     Role: {ADMIN_ROLE}")
        
    except Exception as e:
        print(f"[AVISO] Nao foi possivel criar perfil: {e}")
        print(f"        A tabela user_profiles pode nao existir")
        print(f"        O usuario ainda pode fazer login, mas o role vira do user_metadata")

print()
print("="*80)
print("CONFIGURACAO CONCLUIDA!")
print("="*80)
print()
print("Credenciais do usuario admin:")
print(f"  Email: {ADMIN_EMAIL}")
print(f"  Senha: {ADMIN_PASSWORD}")
print()
print("Agora voce pode:")
print("  1. Fazer login no sistema com estas credenciais")
print("  2. Testar a autenticacao com: python diagnose_supabase_auth.py")
print()
print("Certifique-se de que no backend/.env:")
print("  USE_SUPABASE_AUTH=true")
print()
