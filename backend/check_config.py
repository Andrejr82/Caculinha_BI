"""Verifica configuracao Supabase"""
from app.config.settings import get_settings
s = get_settings()
print("=== CONFIGURACAO SUPABASE ===")
print(f"USE_SUPABASE_AUTH: {s.USE_SUPABASE_AUTH}")
print(f"SUPABASE_URL: {s.SUPABASE_URL if s.SUPABASE_URL else 'NAO CONFIGURADO'}")
print(f"SUPABASE_ANON_KEY: {'Configurado' if s.SUPABASE_ANON_KEY else 'NAO CONFIGURADO'}")
print(f"SUPABASE_SERVICE_ROLE_KEY: {'Configurado' if getattr(s, 'SUPABASE_SERVICE_ROLE_KEY', None) else 'NAO CONFIGURADO'}")
print()
print("=== OUTRAS CONFIGURACOES ===")
print(f"USE_SQL_SERVER: {s.USE_SQL_SERVER}")
print(f"FALLBACK_TO_PARQUET: {getattr(s, 'FALLBACK_TO_PARQUET', 'N/A')}")
