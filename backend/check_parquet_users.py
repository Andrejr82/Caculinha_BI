"""
Verifica usuarios no arquivo Parquet
"""
import sys
from pathlib import Path
import duckdb

backend_dir = Path(__file__).parent

# Procura o arquivo users.parquet
possible_paths = [
    backend_dir / "data" / "parquet" / "users.parquet",
    backend_dir.parent / "data" / "parquet" / "users.parquet",
    Path("/app/data/parquet/users.parquet")
]

users_parquet = None
for path in possible_paths:
    if path.exists():
        users_parquet = path
        break

if not users_parquet:
    print("ERRO: Arquivo users.parquet nao encontrado!")
    print("Procurado em:")
    for path in possible_paths:
        print(f"  - {path}")
    sys.exit(1)

print("="*80)
print("USUARIOS NO ARQUIVO PARQUET")
print("="*80)
print()
print(f"Arquivo: {users_parquet}")
print()

try:
    conn = duckdb.connect()
    
    # Lista todos os usuarios
    query = f"SELECT id, username, email, role, is_active FROM read_parquet('{users_parquet}')"
    result = conn.execute(query).fetchall()
    columns = [desc[0] for desc in conn.description]
    
    print(f"Total de usuarios: {len(result)}")
    print()
    
    for row in result:
        user = dict(zip(columns, row))
        print(f"ID: {user['id']}")
        print(f"  Username: {user['username']}")
        print(f"  Email: {user.get('email', 'N/A')}")
        print(f"  Role: {user['role']}")
        print(f"  Ativo: {user['is_active']}")
        print()
    
    # Verifica se admin existe
    admin_query = f"SELECT * FROM read_parquet('{users_parquet}') WHERE username = 'admin'"
    admin_result = conn.execute(admin_query).fetchall()
    
    if admin_result:
        print("-" * 80)
        print("USUARIO ADMIN ENCONTRADO!")
        print("-" * 80)
        
        admin_columns = [desc[0] for desc in conn.description]
        admin = dict(zip(admin_columns, admin_result[0]))
        
        print(f"ID: {admin['id']}")
        print(f"Username: {admin['username']}")
        print(f"Email: {admin.get('email', 'N/A')}")
        print(f"Role: {admin['role']}")
        print(f"Ativo: {admin['is_active']}")
        print(f"Hash da senha: {admin.get('hashed_password', 'N/A')[:50]}...")
        
        # Testa a senha
        print()
        print("Testando senha 'admin123'...")
        
        import bcrypt
        test_password = "admin123"
        hashed = admin.get('hashed_password', '')
        
        try:
            is_valid = bcrypt.checkpw(
                test_password.encode('utf-8'),
                hashed.encode('utf-8')
            )
            
            if is_valid:
                print("[OK] Senha 'admin123' esta CORRETA!")
            else:
                print("[ERRO] Senha 'admin123' esta INCORRETA!")
        except Exception as e:
            print(f"[ERRO] Falha ao verificar senha: {e}")
    else:
        print("-" * 80)
        print("USUARIO ADMIN NAO ENCONTRADO NO PARQUET!")
        print("-" * 80)
        print()
        print("Voce pode criar o usuario admin executando:")
        print("  python scripts/create_admin_user.py")
    
    conn.close()
    
except Exception as e:
    print(f"ERRO ao ler arquivo Parquet: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*80)
print("RECOMENDACAO")
print("="*80)
print()
print("Para usar autenticacao Parquet (mais simples):")
print("  1. Edite backend/.env:")
print("     USE_SUPABASE_AUTH=false")
print("     FALLBACK_TO_PARQUET=true")
print()
print("  2. Certifique-se de que o usuario admin existe no users.parquet")
print()
print("  3. Reinicie o backend")
print()
