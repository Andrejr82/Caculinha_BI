"""
Teste de Regressão: Garantir que consultas com muitos resultados funcionem
Bug Original: Limite hardcoded de 50 impedia queries com mais de 50 resultados
"""
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

def test_large_result_queries():
    print("=== TESTE DE REGRESSÃO: Queries com Muitos Resultados ===\n")
    
    from app.core.tools.flexible_query_tool import consultar_dados_flexivel
    
    # Teste 1: Query com limite padrão (deve ser 100 agora)
    print("1. Testando limite padrão...")
    result1 = consultar_dados_flexivel(
        filtros={"produto": 369947},
        colunas=["UNE", "UNE_NOME", "VENDA_30DD"],
        ordenar_por="VENDA_30DD"
    )
    
    total1 = result1.get("total_resultados", 0)
    print(f"   Resultados com limite padrão: {total1}")
    
    if total1 < 35:
        print(f"   ⚠️ AVISO: Esperava pelo menos 35 UNEs, recebeu {total1}")
        print("   Isso pode indicar que o limite ainda está muito baixo.")
    else:
        print(f"   ✅ OK: Recebeu {total1} resultados (>= 35)")
    
    # Teste 2: Query com limite explícito de 100
    print("\n2. Testando limite explícito de 100...")
    result2 = consultar_dados_flexivel(
        filtros={"produto": 369947},
        colunas=["UNE", "UNE_NOME", "VENDA_30DD"],
        ordenar_por="VENDA_30DD",
        limite=100
    )
    
    total2 = result2.get("total_resultados", 0)
    print(f"   Resultados com limite=100: {total2}")
    
    if total2 >= 35:
        print(f"   ✅ OK: Recebeu todas as {total2} UNEs")
    else:
        print(f"   ❌ FALHA: Esperava 35 UNEs, recebeu apenas {total2}")
    
    # Teste 3: Query com limite muito alto (deve ser cortado em 500)
    print("\n3. Testando limite máximo (500)...")
    result3 = consultar_dados_flexivel(
        filtros={},  # Sem filtro = todas as linhas
        colunas=["UNE", "PRODUTO"],
        limite=1000  # Deve ser cortado para 500
    )
    
    total3 = result3.get("total_resultados", 0)
    print(f"   Resultados com limite=1000: {total3}")
    
    if total3 == 500:
        print(f"   ✅ OK: Limite máximo de 500 aplicado corretamente")
    elif total3 < 500:
        print(f"   ⚠️ AVISO: Recebeu {total3} resultados (menos que o máximo)")
    else:
        print(f"   ❌ FALHA: Recebeu {total3} resultados (mais que o máximo de 500)")
    
    # Conclusão
    print("\n=== CONCLUSÃO ===")
    if total1 >= 35 and total2 >= 35 and total3 <= 500:
        print("✅ SUCESSO: Todos os testes passaram!")
        print("   O bug de limite foi corrigido.")
    else:
        print("❌ FALHA: Alguns testes falharam.")
        print("   Verifique os logs acima.")

if __name__ == "__main__":
    test_large_result_queries()
