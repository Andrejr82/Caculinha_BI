"""
Cria usuario admin no Supabase Auth e tabela user_profiles
Usa a Service Role Key para operacoes administrativas
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("="*60)
print("CRIAR USUARIO ADMIN NO SUPABASE")
print("="*60)
print()

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("[ERRO] SUPABASE_SERVICE_ROLE_KEY nao configurada no .env")
    print()
    print("Configure no arquivo backend/.env:")
    print("  SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key_aqui")
    print()
    print("Para obter a Service Role Key:")
    print("  1. Va para: https://supabase.com/dashboard")
    print("  2. Selecione seu projeto")
    print("  3. Settings > API")
    print("  4. Copie a 'service_role' key")
    exit(1)

from supabase import create_client
from supabase.lib.client_options import ClientOptions

# Cliente admin
admin_client = create_client(
    SUPABASE_URL, 
    SUPABASE_SERVICE_KEY,
    options=ClientOptions(auto_refresh_token=False, persist_session=False)
)

ADMIN_EMAIL = "admin@agentbi.com"
ADMIN_PASSWORD = "admin"
ADMIN_USERNAME = "admin"

print(f"[1] Verificando se usuario existe: {ADMIN_EMAIL}")

# Verifica se ja existe
try:
    users = admin_client.auth.admin.list_users()
    existing = None
    for user in users:
        if user.email == ADMIN_EMAIL:
            existing = user
            break
    
    if existing:
        print(f"[OK] Usuario ja existe! ID: {existing.id}")
        print()
        print("[2] Atualizando senha para: admin")
        
        # Atualiza senha
        admin_client.auth.admin.update_user_by_id(
            existing.id,
            {"password": ADMIN_PASSWORD}
        )
        print("[OK] Senha atualizada!")
        user_id = existing.id
    else:
        print("[INFO] Usuario nao existe. Criando...")
        
        # Cria usuario
        new_user = admin_client.auth.admin.create_user({
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "email_confirm": True,
            "user_metadata": {"role": "admin", "username": "admin"}
        })
        user_id = new_user.user.id
        print(f"[OK] Usuario criado! ID: {user_id}")
        
except Exception as e:
    print(f"[ERRO] Falha: {e}")
    exit(1)

print()
print("[3] Atualizando tabela user_profiles")

try:
    # Verifica se perfil existe
    profile_resp = admin_client.table("user_profiles").select("*").eq("id", user_id).execute()
    
    if profile_resp.data:
        print("[INFO] Perfil existe. Atualizando role para 'admin'...")
        admin_client.table("user_profiles").update({"role": "admin"}).eq("id", user_id).execute()
        print("[OK] Role atualizado para 'admin'!")
    else:
        print("[INFO] Perfil nao existe. Criando...")
        admin_client.table("user_profiles").insert({
            "id": user_id,
            "username": ADMIN_USERNAME,
            "role": "admin"
        }).execute()
        print("[OK] Perfil criado com role='admin'!")
        
except Exception as e:
    print(f"[AVISO] Erro com user_profiles: {e}")
    print("        O usuario pode funcionar sem a tabela user_profiles")
    print("        usando o role do user_metadata")

print()
print("="*60)
print("[SUCESSO] Usuario admin configurado no Supabase!")
print("="*60)
print()
print("Credenciais:")
print(f"  Email: {ADMIN_EMAIL}")
print(f"  Senha: {ADMIN_PASSWORD}")
print(f"  Role: admin")
print()
print("Reinicie o backend e tente fazer login novamente!")
print()
