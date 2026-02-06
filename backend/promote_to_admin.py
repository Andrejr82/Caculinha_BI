"""
Script para promover usuário para Admin no Supabase
Uso: python promote_to_admin.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ ERRO: Variáveis SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não encontradas!")
    exit(1)

# Usuário a ser promovido (busca por username)
TARGET_USERNAME = "user"
NEW_ROLE = "admin"

print(f"🔧 Conectando ao Supabase: {SUPABASE_URL}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# 1. Buscar usuário na tabela user_profiles por username
print(f"\n📍 Buscando usuário: {TARGET_USERNAME}")
response = supabase.table("user_profiles").select("*").eq("username", TARGET_USERNAME).execute()

if not response.data or len(response.data) == 0:
    print(f"❌ Usuário '{TARGET_USERNAME}' não encontrado na tabela 'user_profiles'")
    print("\n📊 Listando todos os perfis existentes:")
    all_profiles = supabase.table("user_profiles").select("id, username, role").execute()
    for p in all_profiles.data:
        print(f"   - Username: {p.get('username', 'N/A')} | Role: {p.get('role', 'N/A')}")
    exit(1)

user_data = response.data[0]
user_id = user_data.get("id")
current_role = user_data.get("role", "user")

print(f"✅ Usuário encontrado!")
print(f"   ID: {user_id}")
print(f"   Username: {user_data.get('username', 'N/A')}")
print(f"   Role Atual: {current_role}")

if current_role == NEW_ROLE:
    print(f"\n⚠️  Usuário já possui role '{NEW_ROLE}'. Nenhuma alteração necessária.")
    exit(0)

# 2. Atualizar role para admin
print(f"\n🚀 Atualizando role de '{current_role}' para '{NEW_ROLE}'...")
update_response = supabase.table("user_profiles").update({
    "role": NEW_ROLE
}).eq("id", user_id).execute()

if update_response.data:
    print(f"✅ SUCESSO! Usuário '{TARGET_USERNAME}' agora é '{NEW_ROLE}'!")
    print("\n📋 Dados atualizados:")
    for key, value in update_response.data[0].items():
        print(f"   {key}: {value}")
else:
    print(f"❌ Falha ao atualizar. Resposta: {update_response}")
