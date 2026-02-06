"""
Script Simples de Verificação - Configurações
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("\n" + "="*60)
print("  VERIFICAÇÃO RÁPIDA - CONFIGURAÇÕES")
print("="*60 + "\n")

try:
    from app.config.settings import get_settings
    settings = get_settings()
    
    print("✅ Settings carregado com sucesso\n")
    
    print("DATABASE_URL:")
    db_url = str(settings.DATABASE_URL)
    # Mascarar senha
    if "@" in db_url:
        parts = db_url.split("@")
        user_part = parts[0].split("://")[1].split(":")[0]
        safe_url = db_url.split("://")[0] + "://" + user_part + ":***@" + parts[1]
        print(f"  {safe_url}\n")
    else:
        print(f"  {db_url}\n")
    
    print(f"SECRET_KEY: {'*' * len(settings.SECRET_KEY)} ({len(settings.SECRET_KEY)} chars)")
    if len(settings.SECRET_KEY) < 32:
        print("  ⚠️  ATENÇÃO: SECRET_KEY deve ter no mínimo 32 caracteres!\n")
    else:
        print("  ✅ SECRET_KEY tem comprimento adequado\n")
    
    print(f"ALGORITHM: {settings.ALGORITHM}")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    print(f"REFRESH_TOKEN_EXPIRE_DAYS: {settings.REFRESH_TOKEN_EXPIRE_DAYS}")
    
    print("\n" + "="*60 + "\n")
    
except Exception as e:
    print(f"❌ Erro ao carregar settings: {e}")
    import traceback
    print(traceback.format_exc())
