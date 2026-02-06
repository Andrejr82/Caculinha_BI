import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Adicionar diretório atual ao path para importar app
sys.path.append(os.getcwd())

# Carregar variáveis de ambiente
load_dotenv(dotenv_path=".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erro: Credenciais do Supabase não encontradas no .env")
    print(f"URL: {SUPABASE_URL}")
    print(f"KEY: {'DEFINIDA' if SUPABASE_SERVICE_KEY else 'AUSENTE'}")
    sys.exit(1)

print(f"📡 Conectando ao Supabase: {SUPABASE_URL}")
print(f"🔑 Usando Service Role Key")

try:
    # Usar Service Key para ter acesso total (Admin)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # 1. Verificar auth.users (Lista rápida)
    print("\n🔍 Verificando auth.users...")
    users = supabase.auth.admin.list_users()
    print(f"✅ Auth Users encontrados: {len(users) if isinstance(users, list) else len(users.users)}")

    # 2. Listar tabelas públicas (Introspecção simulada)
    print("\n🔍 Testando tabelas conhecidas no schema 'public'...")
    tabelas_candidatas = ['user_profiles', 'usuarios', 'users', 'profiles', 'usuario']
    
    for tabela in tabelas_candidatas:
        try:
            print(f"   > Testando '{tabela}'...", end=" ")
            resp = supabase.table(tabela).select("*").limit(1).execute()
            print(f"✅ EXISTE! (Registros: {len(resp.data) if resp.data else '0/Vazio'})")
            if resp.data:
                print(f"     Colunas detectadas: {list(resp.data[0].keys())}")
        except Exception as e:
            msg = str(e)
            if "RW002" in msg or "404" in msg or "relation" in msg and "does not exist" in msg:
                 print("❌ Não encontrada")
            else:
                 print(f"⚠️ Erro: {msg}")

    print("\n✅ Diagnóstico concluído.")

except Exception as e:
    print(f"❌ Erro crítico de conexão: {e}")
