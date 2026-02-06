"""
Script para corrigir segmentos do Admin no Supabase
Atualiza allowed_segments no auth.users (user_metadata)
"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ ERRO: Variáveis não encontradas!")
    exit(1)

TARGET_EMAIL = "user@agentbi.com"
CORRECT_SEGMENTS = ["*"]  # Admin = acesso total

print(f"🔧 Conectando ao Supabase: {SUPABASE_URL}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# 1. Listar usuários do auth para encontrar o ID
print(f"\n📍 Buscando usuário no auth.users: {TARGET_EMAIL}")
users = supabase.auth.admin.list_users()

target_user = None
for u in users:
    if u.email == TARGET_EMAIL:
        target_user = u
        break

if not target_user:
    print(f"❌ Usuário '{TARGET_EMAIL}' não encontrado no auth.users!")
    print("\n📊 Usuários disponíveis:")
    for u in users[:5]:
        print(f"   - {u.email}")
    exit(1)

print(f"✅ Usuário encontrado!")
print(f"   ID: {target_user.id}")
print(f"   Email: {target_user.email}")
print(f"   Metadata atual: {target_user.user_metadata}")

# 2. Atualizar user_metadata com allowed_segments correto
print(f"\n🚀 Atualizando allowed_segments para {CORRECT_SEGMENTS}...")

current_metadata = target_user.user_metadata or {}
current_metadata["allowed_segments"] = CORRECT_SEGMENTS
current_metadata["role"] = "admin"  # Garantir role admin

update_response = supabase.auth.admin.update_user_by_id(
    target_user.id,
    {"user_metadata": current_metadata}
)

if update_response:
    print(f"✅ SUCESSO! Metadata atualizado!")
    print(f"\n📋 Novo user_metadata:")
    print(f"   {update_response.user.user_metadata}")
else:
    print(f"❌ Falha ao atualizar.")
