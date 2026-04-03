import os
import sys
import pyodbc
from pathlib import Path

# Adiciona o diretório backend ao path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.config.settings import get_settings
from supabase import create_client, Client

# Configurações SQL Server via variáveis de ambiente
_conn_str = os.environ.get("PYODBC_CONNECTION_STRING", "")
if not _conn_str:
    _srv = os.environ.get("DB_ALT_SERVER", "localhost,1433")
    _db  = os.environ.get("DB_ALT_DATABASE", "agentbi")
    _uid = os.environ.get("DB_ALT_USER", "AgenteVirtual")
    _pwd = os.environ.get("DB_ALT_PASSWORD", "")
    if not _pwd:
        raise SystemExit("Erro: defina PYODBC_CONNECTION_STRING ou DB_ALT_PASSWORD antes de executar.")
    _conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={_srv};DATABASE={_db};UID={_uid};PWD={_pwd};TrustServerCertificate=yes;"
CONN_STR = _conn_str

def sync_users():
    settings = get_settings()
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Supabase não configurado.")
        return

    print("--- Iniciando Sincronização Supabase -> SQL Server (Ajustado) ---")
    
    try:
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        
        profiles = supabase.table("user_profiles").select("*").execute()
        
        for profile in profiles.data:
            supabase_id = profile['id']
            username = profile['username']
            role = profile.get('role', 'user')
            email = f"{username}@agentbi.com"
            
            print(f"Sincronizando: {username}...")

            # 1. Verificar se o ID já existe
            cursor.execute("SELECT id FROM users WHERE id = ?", (supabase_id,))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET username=?, email=?, role=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", 
                             (username, email, role, supabase_id))
                print(f"  -> ID {supabase_id} atualizado.")
                continue

            # 2. Se o ID não existe, verificar se o USERNAME ou EMAIL existe (conflito de migração)
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            row = cursor.fetchone()
            if row:
                old_id = row[0]
                print(f"  -> Conflito: Usuário existe com ID antigo {old_id}. Atualizando para ID do Supabase...")
                cursor.execute("UPDATE users SET id = ?, role = ? WHERE id = ?", (supabase_id, role, old_id))
            else:
                # 3. Criar novo
                dummy_hash = "EXTERNAL_AUTH_SUPABASE"
                cursor.execute("""
                    INSERT INTO users (id, username, email, hashed_password, role, is_active, allowed_segments)
                    VALUES (?, ?, ?, ?, ?, 1, '[]')
                """, (supabase_id, username, email, dummy_hash, role))
                print(f"  -> Criado novo registro.")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("\n✅ Sincronização concluída!")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    sync_users()
