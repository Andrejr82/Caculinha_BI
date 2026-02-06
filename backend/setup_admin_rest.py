"""
Cria usuario admin no Supabase usando API REST direta
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("="*60)
print("CRIAR USUARIO ADMIN NO SUPABASE (via API REST)")
print("="*60)
print()

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("[ERRO] SUPABASE_SERVICE_ROLE_KEY nao configurada")
    exit(1)

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json"
}

ADMIN_EMAIL = "admin@agentbi.com"
ADMIN_PASSWORD = "admin123"  # Supabase requer minimo 6 caracteres

# 1. Listar usuarios
print("[1] Listando usuarios existentes...")
list_url = f"{SUPABASE_URL}/auth/v1/admin/users"
resp = requests.get(list_url, headers=headers)

if resp.status_code == 200:
    users = resp.json().get("users", [])
    print(f"    Encontrados: {len(users)} usuarios")
    
    existing = None
    for u in users:
        if u.get("email") == ADMIN_EMAIL:
            existing = u
            print(f"    [INFO] Admin ja existe! ID: {u['id']}")
            break
else:
    print(f"[AVISO] Erro ao listar: {resp.status_code}")
    users = []
    existing = None

# 2. Criar ou atualizar
if existing:
    print()
    print("[2] Atualizando senha do admin...")
    update_url = f"{SUPABASE_URL}/auth/v1/admin/users/{existing['id']}"
    update_data = {"password": ADMIN_PASSWORD}
    resp = requests.put(update_url, headers=headers, json=update_data)
    
    if resp.status_code == 200:
        print("    [OK] Senha atualizada para: admin")
        user_id = existing['id']
    else:
        print(f"    [ERRO] Falha: {resp.text}")
        exit(1)
else:
    print()
    print("[2] Criando usuario admin...")
    create_url = f"{SUPABASE_URL}/auth/v1/admin/users"
    create_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "email_confirm": True,
        "user_metadata": {"role": "admin", "username": "admin"}
    }
    resp = requests.post(create_url, headers=headers, json=create_data)
    
    if resp.status_code in [200, 201]:
        user_data = resp.json()
        user_id = user_data.get("id")
        print(f"    [OK] Usuario criado! ID: {user_id}")
    else:
        print(f"    [ERRO] Falha: {resp.text}")
        exit(1)

# 3. Atualizar tabela user_profiles
print()
print("[3] Atualizando tabela user_profiles...")
profile_url = f"{SUPABASE_URL}/rest/v1/user_profiles"

# Verifica se existe
check_resp = requests.get(
    f"{profile_url}?id=eq.{user_id}",
    headers={**headers, "Prefer": "return=representation"}
)

if check_resp.status_code == 200 and check_resp.json():
    print("    [INFO] Perfil existe. Atualizando role...")
    update_resp = requests.patch(
        f"{profile_url}?id=eq.{user_id}",
        headers={**headers, "Prefer": "return=representation"},
        json={"role": "admin"}
    )
    if update_resp.status_code in [200, 204]:
        print("    [OK] Role atualizado para 'admin'")
    else:
        print(f"    [AVISO] Erro ao atualizar: {update_resp.text}")
else:
    print("    [INFO] Perfil nao existe. Criando...")
    insert_resp = requests.post(
        profile_url,
        headers={**headers, "Prefer": "return=representation"},
        json={"id": user_id, "username": "admin", "role": "admin"}
    )
    if insert_resp.status_code in [200, 201]:
        print("    [OK] Perfil criado!")
    else:
        print(f"    [AVISO] Erro ao criar: {insert_resp.text}")
        print("    O usuario ainda funcionara com role do metadata")

print()
print("="*60)
print("[SUCESSO] Admin configurado!")
print("="*60)
print()
print("Credenciais:")
print(f"  Email: {ADMIN_EMAIL}")
print(f"  Senha: {ADMIN_PASSWORD}")
print()
print("Reinicie o backend e tente login com:")
print("  Usuario: admin")
print("  Senha: admin")
print()
