"""
Teste rápido da lógica de sazonalidade
"""
from datetime import datetime
import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.utils.seasonality_detector import detect_seasonal_context

print("="*80)
print("TESTE RÁPIDO - DETECÇÃO DE SAZONALIDADE POR SEGMENTO")
print("="*80)

# Teste 1: PAPELARIA em Janeiro (deve ter sazonalidade)
print("\n1. PAPELARIA em Janeiro:")
ctx1 = detect_seasonal_context(
    reference_date=datetime(2026, 1, 15),
    produto_segmento="PAPELARIA"
)
if ctx1:
    print(f"   ✅ Sazonalidade: {ctx1['season'].upper()}")
    print(f"   ✅ Multiplicador: {ctx1['multiplier']}x")
else:
    print("   ❌ ERRO: Deveria ter sazonalidade VOLTA_AS_AULAS")

# Teste 2: CASA E DECORAÇÃO em Janeiro (NÃO deve ter sazonalidade)
print("\n2. CASA E DECORAÇÃO em Janeiro:")
ctx2 = detect_seasonal_context(
    reference_date=datetime(2026, 1, 15),
    produto_segmento="CASA E DECORAÇÃO"
)
if ctx2:
    print(f"   ❌ ERRO: Não deveria ter sazonalidade")
    print(f"   ❌ Detectado: {ctx2['season'].upper()}")
else:
    print("   ✅ CORRETO: Sem sazonalidade (como esperado)")

# Teste 3: CASA E DECORAÇÃO em Dezembro (deve ter sazonalidade NATAL)
print("\n3. CASA E DECORAÇÃO em Dezembro:")
ctx3 = detect_seasonal_context(
    reference_date=datetime(2026, 12, 15),
    produto_segmento="CASA E DECORAÇÃO"
)
if ctx3:
    print(f"   ✅ Sazonalidade: {ctx3['season'].upper()}")
    print(f"   ✅ Multiplicador: {ctx3['multiplier']}x")
else:
    print("   ❌ ERRO: Deveria ter sazonalidade NATAL")

# Teste 4: Case insensitive
print("\n4. Case Insensitive (papelaria em lowercase):")
ctx4 = detect_seasonal_context(
    reference_date=datetime(2026, 1, 15),
    produto_segmento="papelaria"
)
if ctx4:
    print(f"   ✅ Funciona com lowercase: {ctx4['season'].upper()}")
else:
    print("   ❌ ERRO: Deveria funcionar com lowercase")

print("\n" + "="*80)
print("RESUMO:")
print("="*80)
print(f"Teste 1 (PAPELARIA Jan): {'✅ PASSOU' if ctx1 else '❌ FALHOU'}")
print(f"Teste 2 (CASA Dez Jan): {'✅ PASSOU' if not ctx2 else '❌ FALHOU'}")
print(f"Teste 3 (CASA Dez Dez): {'✅ PASSOU' if ctx3 else '❌ FALHOU'}")
print(f"Teste 4 (Case Insensitive): {'✅ PASSOU' if ctx4 else '❌ FALHOU'}")

all_passed = ctx1 and not ctx2 and ctx3 and ctx4
print(f"\n{'✅ TODOS OS TESTES PASSARAM!' if all_passed else '❌ ALGUNS TESTES FALHARAM'}")
print("="*80)
