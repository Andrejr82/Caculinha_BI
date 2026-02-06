"""
Script para corrigir senha do usuario admin
"""
import bcrypt
import duckdb
from pathlib import Path

# Caminho do arquivo
parquet_path = Path("data/parquet/users.parquet")

if not parquet_path.exists():
    print(f"[ERRO] Arquivo nao encontrado: {parquet_path}")
    exit(1)

# Gera hash da nova senha
password = "admin"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"[OK] Hash gerado para senha: {password}")

# Le o arquivo atual
conn = duckdb.connect()
parquet_str = str(parquet_path).replace("\\", "/")
df = conn.execute(f"SELECT * FROM read_parquet('{parquet_str}')").df()
print(f"[OK] Usuarios encontrados: {len(df)}")
print(f"     Usuarios: {df['username'].tolist()}")

# Atualiza a senha do admin
df.loc[df['username'] == 'admin', 'hashed_password'] = hashed
print("[OK] Senha do admin atualizada no DataFrame")

# Salva de volta
conn.execute(f"COPY df TO '{parquet_str}' (FORMAT PARQUET)")
conn.close()

print()
print("="*50)
print("[SUCESSO] Usuario admin atualizado!")
print("="*50)
print()
print("Credenciais:")
print("  Usuario: admin")
print("  Senha:   admin")
print()
