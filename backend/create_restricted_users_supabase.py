"""
Criar usuários com segmentos restritos no Supabase.
Demonstra que a restrição por segmento funciona corretamente.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("[ERRO] Credenciais do Supabase não configuradas no .env")
    sys.exit(1)

# Users com segmentos restritos
test_users = [
    {
        "email": "analista.tecidos@cacaulinha.com",
        "password": "test123",
        "username": "analista_tecidos",
        "role": "user",
        "allowed_segments": ["TECIDOS"]  # Somente TECIDOS
    },
    {
        "email": "analista.armarinho@cacaulinha.com",
        "password": "test123",
        "username": "analista_armarinho",
        "role": "user",
        "allowed_segments": ["ARMARINHO"]  # Somente ARMARINHO
    },
    {
        "email": "gerente.loja@cacaulinha.com",
        "password": "test123",
        "username": "gerente_loja",
        "role": "user",
        "allowed_segments": ["TECIDOS", "ARMARINHO", "PAPELARIA"]  # Múltiplos
    }
]

print("=" * 80)
print("CRIANDO USUARIOS COM SEGMENTOS RESTRITOS NO SUPABASE")
print("=" * 80)
print()

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print(f"[OK] Conectado ao Supabase: {SUPABASE_URL}")
    print()

    for user_data in test_users:
        print(f"[PROCESSANDO] {user_data['username']}")
        print(f"  Email: {user_data['email']}")
        print(f"  Segmentos: {user_data['allowed_segments']}")

        try:
            # Check if user exists
            existing = supabase.auth.admin.list_users()
            user_exists = any(u.email == user_data['email'] for u in existing if existing)

            if user_exists:
                print(f"  [AVISO] Usuario ja existe - pulando criacao")
                print()
                continue

            # Create auth user
            auth_result = supabase.auth.admin.create_user({
                "email": user_data['email'],
                "password": user_data['password'],
                "email_confirm": True,
                "user_metadata": {
                    "username": user_data['username'],
                    "role": user_data['role']
                }
            })

            if not auth_result or not auth_result.user:
                print(f"  [ERRO] Falha ao criar usuario auth")
                continue

            user_id = str(auth_result.user.id)
            print(f"  [OK] Usuario auth criado - ID: {user_id}")

            # Create user_profiles entry
            profile_data = {
                "id": user_id,
                "username": user_data['username'],
                "role": user_data['role']
            }

            supabase.table("user_profiles").insert(profile_data).execute()
            print(f"  [OK] Perfil criado")

            # Create user_segments entries
            for segment in user_data['allowed_segments']:
                segment_data = {
                    "user_id": user_id,
                    "segment": segment
                }
                supabase.table("user_segments").insert(segment_data).execute()

            print(f"  [OK] Segmentos configurados: {user_data['allowed_segments']}")
            print()

        except Exception as e:
            print(f"  [ERRO] {e}")
            print()
            continue

    print("=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)
    print()
    print("Usuarios criados com segmentos restritos:")
    print()
    for user_data in test_users:
        print(f"  {user_data['username']:25s} -> {user_data['allowed_segments']}")
    print()
    print("Teste de login:")
    print(f"  curl -X POST http://localhost:8000/api/v1/auth/login \\")
    print(f"       -H 'Content-Type: application/json' \\")
    print(f"       -d '{{\"username\":\"analista_tecidos\",\"password\":\"test123\"}}'")
    print()

except Exception as e:
    print(f"[ERRO FATAL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
