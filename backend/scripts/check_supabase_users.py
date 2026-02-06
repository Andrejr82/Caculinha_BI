
import os
import sys
from pathlib import Path

# Adiciona o diretório backend ao path para importar as configurações
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config.settings import get_settings
from supabase import create_client, Client

USERS_TO_CHECK = ["lucas.garcia", "hugo.mendes", "fausto.neto"]

def check_supabase():
    settings = get_settings()
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Chaves do Supabase não configuradas no .env")
        return

    print("--- Verificando Supabase ---")
    try:
        # Usa a SERVICE_ROLE_KEY para poder listar usuários ou consultar tabelas protegidas
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # 1. Verificar na tabela user_profiles (onde costumam ficar os metadados vinculados ao username)
        print("Consultando tabela 'user_profiles'...")
        for username in USERS_TO_CHECK:
            response = supabase.table("user_profiles").select("id, username, role").eq("username", username).execute()
            
            if response.data and len(response.data) > 0:
                user = response.data[0]
                print(f"✅ Usuário '{username}' encontrado em user_profiles! (ID: {user['id']}, Role: {user['role']})")
            else:
                print(f"❌ Usuário '{username}' NÃO encontrado em user_profiles.")
                
        # 2. Opcionalmente, verificar se existem emails correspondentes no Auth (se tivermos permissão)
        print("\nVerificando possíveis emails no Auth...")
        for username in USERS_TO_CHECK:
            email = f"{username}@agentbi.com"
            # No Supabase Python, admin.list_users() é o caminho, mas vamos tentar por busca simples de perfil primeiro
            # para evitar erros de permissão se a service_key não for plena
            pass

    except Exception as e:
        print(f"Erro ao consultar Supabase: {e}")

if __name__ == "__main__":
    check_supabase()
