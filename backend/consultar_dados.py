import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis
load_dotenv(dotenv_path=".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erro: Credenciais ausentes no .env")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print(f"📊 CONSULTA DETALHADA SUPABASE ({SUPABASE_URL})")
print("-" * 50)

# 1. auth.users
try:
    print("\n1️⃣ Tabela 'auth.users' (Sistema de Login):")
    users = supabase.auth.admin.list_users()
    if users:
        print(f"   Total: {len(users)}")
        for i, u in enumerate(users[:5]): # Top 5
            print(f"   [{i+1}] Email: {u.email} | ID: {u.id}")
            print(f"       Meta: {u.user_metadata}")
    else:
        print("   (Vazio)")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 2. public.usuarios
try:
    print("\n2️⃣ Tabela 'public.usuarios' (Customizada?):")
    resp = supabase.table("usuarios").select("*").limit(5).execute()
    if resp.data:
        print(f"   Total: {len(resp.data)} (mostrando top 5)")
        cols = list(resp.data[0].keys())
        print(f"   Colunas: {cols}")
        for i, row in enumerate(resp.data):
            # Tentar identificar campos chave
            nome = row.get('username') or row.get('nome') or row.get('email') or 'N/A'
            role = row.get('role') or row.get('perfil') or 'N/A'
            print(f"   [{i+1}] {nome} | Role: {role} | ID: {row.get('id')}")
    else:
        print("   (Vazio ou não existe)")
except Exception as e:
    # Tentar public.users se usuarios falhar
    try:
        print("\n2️⃣ Tentando 'public.users' em vez de 'usuarios'...")
        resp = supabase.table("users").select("*").limit(5).execute()
        if resp.data:
             print(f"   Total: {len(resp.data)}")
             print(f"   Colunas: {list(resp.data[0].keys())}")
        else:
             print("   (Vazio)")
    except Exception as e2:
        print(f"   ❌ Tabela 'usuarios'/'users' não acessível: {e}")

# 3. public.user_profiles (Padrão do Sistema)
try:
    print("\n3️⃣ Tabela 'public.user_profiles' (Padrão Agent BI):")
    resp = supabase.table("user_profiles").select("*").limit(5).execute()
    if resp.data:
        print(f"   Total: {len(resp.data)}")
        for row in resp.data:
            print(f"   - {row.get('username')} ({row.get('role')})")
    else:
        print("   (Vazio ou não existe - Recomendado criar via script)")
except Exception as e:
    print(f"   ❌ Não existe ou erro: {e}")

print("-" * 50)
