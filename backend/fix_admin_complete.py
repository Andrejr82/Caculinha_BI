"""
Correção COMPLETA do usuário admin
Garante:
1. Senha correta: admin
2. Role: admin
3. allowed_segments: ["*"] (acesso global)
"""
import bcrypt
import duckdb
import json
from pathlib import Path

# Caminho do arquivo
parquet_path = Path("data/parquet/users.parquet")

if not parquet_path.exists():
    print(f"[ERRO] Arquivo nao encontrado: {parquet_path}")
    exit(1)

print("="*60)
print("CORRECAO COMPLETA DO USUARIO ADMIN")
print("="*60)
print()

# Gera hash da senha
password = "admin"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"[1] Hash gerado para senha: {password}")

# Le o arquivo atual
conn = duckdb.connect()
parquet_str = str(parquet_path).replace("\\", "/")
df = conn.execute(f"SELECT * FROM read_parquet('{parquet_str}')").df()
print(f"[2] Usuarios encontrados: {len(df)}")

# Mostra estado atual
print()
print("Estado ANTES:")
for _, row in df.iterrows():
    print(f"  - {row['username']}: role={row['role']}, segments={row.get('allowed_segments', 'N/A')}")

# Corrige admin
admin_mask = df['username'] == 'admin'
df.loc[admin_mask, 'hashed_password'] = hashed
df.loc[admin_mask, 'role'] = 'admin'
df.loc[admin_mask, 'allowed_segments'] = '["*"]'  # JSON string com acesso global
df.loc[admin_mask, 'is_active'] = True

print()
print("[3] Correcoes aplicadas ao admin:")
print("    - Senha: admin")
print("    - Role: admin")  
print("    - allowed_segments: ['*'] (acesso global)")
print("    - is_active: True")

# Mostra estado depois
print()
print("Estado DEPOIS:")
for _, row in df.iterrows():
    print(f"  - {row['username']}: role={row['role']}, segments={row.get('allowed_segments', 'N/A')}")

# Salva de volta
conn.execute(f"COPY df TO '{parquet_str}' (FORMAT PARQUET)")
conn.close()

print()
print("="*60)
print("[SUCESSO] Usuario admin corrigido!")
print("="*60)
print()
print("Credenciais:")
print("  Usuario: admin")
print("  Senha:   admin")
print("  Acesso:  GLOBAL (todos os segmentos)")
print()
print("IMPORTANTE: Reinicie o backend para aplicar as alteracoes!")
print()
