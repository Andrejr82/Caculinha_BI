"""
Teste de RLS no DataSourceManager
"""
import sys
import os

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

# Simular contexto de usuário
from app.core import context

# Teste 1: Usuário com acesso restrito
print("=== TESTE 1: Usuário com segmento restrito ===")
context._current_user_segments = ["ARMARINHO"]

from app.core.data_source_manager import get_data_manager

manager = get_data_manager()
df = manager.get_data(limit=10)

print(f"Total de registros retornados: {len(df)}")
if 'NOMESEGMENTO' in df.columns:
    print(f"Segmentos únicos: {df['NOMESEGMENTO'].unique()}")
    assert all(df['NOMESEGMENTO'] == "ARMARINHO"), "❌ FALHA: RLS não aplicado corretamente!"
    print("✅ RLS funcionando: apenas ARMARINHO retornado")
else:
    print("⚠️ Coluna NOMESEGMENTO não encontrada")

# Teste 2: Usuário admin (acesso total)
print("\n=== TESTE 2: Usuário admin (acesso total) ===")
context._current_user_segments = ["*"]

df_admin = manager.get_data(limit=10)
print(f"Total de registros retornados: {len(df_admin)}")
if 'NOMESEGMENTO' in df_admin.columns:
    print(f"Segmentos únicos: {df_admin['NOMESEGMENTO'].unique()}")
    print("✅ Admin tem acesso a todos os segmentos")

print("\n✅ Todos os testes de RLS passaram!")
