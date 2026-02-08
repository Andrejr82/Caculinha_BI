import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("backend/.env"))

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("ERRO: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY nao configurados")
    exit(1)

client = create_client(url, key)
users = client.auth.admin.list_users()

print("=" * 60)
print("USUARIOS NO SUPABASE")
print("=" * 60)

if not users:
    print("Nenhum usuario encontrado!")
else:
    for u in users:
        role = "user"
        if u.user_metadata:
            role = u.user_metadata.get("role", "user")
        print(f"  Email: {u.email}")
        print(f"  Role: {role}")
        print(f"  ID: {u.id}")
        print("-" * 40)

print(f"\nTotal: {len(users)} usuarios")
