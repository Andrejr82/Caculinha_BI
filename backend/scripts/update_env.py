"""
Atualizar DATABASE_URL no arquivo .env do backend
"""

import os
from pathlib import Path

print("\n" + "="*70)
print("  🔧 ATUALIZAR DATABASE_URL NO .ENV")
print("="*70 + "\n")

# Caminho do arquivo .env
env_file = Path(__file__).parent.parent / ".env"

# Nova DATABASE_URL — lida de variáveis de ambiente
_user = os.environ.get("DB_ALT_USER", "AgenteVirtual")
_pwd  = os.environ.get("DB_ALT_PASSWORD", "")
_host = os.environ.get("DB_ALT_SERVER", "127.0.0.1,1433").replace(",", ":")
_db   = os.environ.get("DB_ALT_DATABASE", "Projeto_Caculinha")

if not _pwd:
    raise SystemExit(
        "Erro: defina DB_ALT_PASSWORD antes de executar este script.\n"
        "Exemplo: $env:DB_ALT_PASSWORD='suasenha'; python scripts/update_env.py"
    )

new_database_url = (
    f"mssql+aioodbc://{_user}:{_pwd}@{_host}/{_db}"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
)


print(f"Arquivo: {env_file}")
print(f"\nNova DATABASE_URL:")
print(f"  {new_database_url}\n")

try:
    # Ler arquivo .env
    if not env_file.exists():
        print(f"❌ Arquivo .env não encontrado em: {env_file}")
        print("\nCriando arquivo .env...")
        
        # Criar .env básico
        env_content = f"""# Backend Environment Variables - SQL Server

# App
APP_NAME="Agent BI Backend"
APP_VERSION="1.0.0"
DEBUG=true
ENVIRONMENT=development

# API
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Database - SQL Server
DATABASE_URL={new_database_url}

# Hybrid Architecture Flags
USE_SQL_SERVER=true
FALLBACK_TO_PARQUET=true
SQL_SERVER_TIMEOUT=10

DB_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Security
SECRET_KEY=your-secret-key-change-in-production-min-32-chars-long-please-use-strong-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_AUTH_PER_MINUTE=5

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Metrics
METRICS_ENABLED=true
"""
        env_file.write_text(env_content, encoding="utf-8")
        print("✅ Arquivo .env criado com sucesso!")
        
    else:
        # Ler conteúdo existente
        content = env_file.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        # Atualizar linha DATABASE_URL
        updated = False
        new_lines = []
        
        for line in lines:
            if line.strip().startswith("DATABASE_URL="):
                new_lines.append(f"DATABASE_URL={new_database_url}")
                updated = True
                print("✅ Linha DATABASE_URL atualizada")
            else:
                new_lines.append(line)
        
        # Se não encontrou, adicionar
        if not updated:
            print("⚠️  DATABASE_URL não encontrado, adicionando...")
            # Procurar seção Database
            for i, line in enumerate(new_lines):
                if "# Database" in line or "DATABASE" in line:
                    new_lines.insert(i + 1, f"DATABASE_URL={new_database_url}")
                    break
            else:
                # Se não encontrou seção, adicionar no final
                new_lines.append(f"\n# Database - SQL Server")
                new_lines.append(f"DATABASE_URL={new_database_url}")
        
        # Salvar arquivo
        env_file.write_text("\n".join(new_lines), encoding="utf-8")
        print("✅ Arquivo .env atualizado com sucesso!")
    
    print("\n" + "="*70)
    print("  ✅ CONFIGURAÇÃO CONCLUÍDA!")
    print("="*70 + "\n")
    
    print("Próximos passos:")
    print("  1. Executar: alembic upgrade head")
    print("  2. Executar: python scripts\\seed_admin.py")
    print("  3. Executar: python scripts\\check_admin.py")
    print()

except Exception as e:
    print(f"❌ Erro ao atualizar .env: {e}")
    import traceback
    traceback.print_exc()
