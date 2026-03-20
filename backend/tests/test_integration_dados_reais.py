"""
Integration Tests: Validação com Dados Reais
Testa comportamento usando queries SQL diretas no Parquet
Seguindo AAA Pattern (Arrange, Act, Assert)
"""
import sys
import os
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.realdata]

if os.getenv("RUN_REALDATA_TESTS", "0") != "1":
    pytest.skip(
        "teste com dados reais; defina RUN_REALDATA_TESTS=1 para executar.",
        allow_module_level=True,
    )

# Adicionar backend ao path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

def test_produto_369947_tem_35_unes():
    """
    DADO: Produto 369947 no banco de dados real
    QUANDO: Consultar quantas UNEs têm vendas
    ENTÃO: Deve retornar ~35 UNEs
    """
    # Arrange
    from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
    
    adapter = get_duckdb_adapter()
    
    # Act
    query = """
    SELECT 
        UNE,
        UNE_NOME,
        VENDA_30DD,
        ESTOQUE_UNE
    FROM read_parquet('data/parquet/admmat.parquet')
    WHERE PRODUTO = 369947 AND VENDA_30DD > 0
    ORDER BY VENDA_30DD DESC
    """
    
    result = adapter.query(query)
    total_unes = len(result)
    
    # Assert
    assert total_unes >= 35, f"Esperava >= 35 UNEs, encontrou {total_unes}"
    assert total_unes <= 40, f"Esperava <= 40 UNEs, encontrou {total_unes}"
    
    print(f"✅ PASS: Produto 369947 tem {total_unes} UNEs com vendas")
    print(f"   Top 3 UNEs:")
    for i in range(min(3, len(result))):
        print(f"   {i+1}. UNE {result['UNE'][i]}: {result['VENDA_30DD'][i]} vendas")

def test_limite_100_retorna_100_registros():
    """
    DADO: Query com LIMIT 100
    QUANDO: Executar no DuckDB
    ENTÃO: Deve retornar exatamente 100 registros
    """
    # Arrange
    from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
    
    adapter = get_duckdb_adapter()
    
    # Act
    query = """
    SELECT UNE, PRODUTO
    FROM read_parquet('data/parquet/admmat.parquet')
    LIMIT 100
    """
    
    result = adapter.query(query)
    total = len(result)
    
    # Assert
    assert total == 100, f"Esperava 100 registros, recebeu {total}"
    print(f"✅ PASS: LIMIT 100 retornou {total} registros")

def test_limite_500_retorna_500_registros():
    """
    DADO: Query com LIMIT 500
    QUANDO: Executar no DuckDB
    ENTÃO: Deve retornar exatamente 500 registros
    """
    # Arrange
    from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
    
    adapter = get_duckdb_adapter()
    
    # Act
    query = """
    SELECT UNE, PRODUTO
    FROM read_parquet('data/parquet/admmat.parquet')
    LIMIT 500
    """
    
    result = adapter.query(query)
    total = len(result)
    
    # Assert
    assert total == 500, f"Esperava 500 registros, recebeu {total}"
    print(f"✅ PASS: LIMIT 500 retornou {total} registros")

def test_produto_369947_todas_unes_sem_limite():
    """
    DADO: Produto 369947 com 35 UNEs
    QUANDO: Consultar SEM limite
    ENTÃO: Deve retornar TODAS as UNEs (não apenas 9-20)
    """
    # Arrange
    from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
    
    adapter = get_duckdb_adapter()
    
    # Act
    query = """
    SELECT COUNT(DISTINCT UNE) as total_unes
    FROM read_parquet('data/parquet/admmat.parquet')
    WHERE PRODUTO = 369947 AND VENDA_30DD > 0
    """
    
    result = adapter.query(query)
    total_unes = result['total_unes'][0]
    
    # Assert
    assert total_unes >= 35, f"Esperava >= 35 UNEs, encontrou {total_unes}"
    
    print(f"✅ PASS: Produto 369947 tem {total_unes} UNEs (SEM limite)")
    print(f"   ANTES da correção: ferramenta retornava apenas ~9-20")
    print(f"   DEPOIS da correção: ferramenta deve retornar todas as {total_unes}")

def test_agregacao_top_10_unes():
    """
    DADO: Produto 369947
    QUANDO: Agregar vendas por UNE e limitar a 10
    ENTÃO: Deve retornar top 10 UNEs por vendas
    """
    # Arrange
    from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
    
    adapter = get_duckdb_adapter()
    
    # Act
    query = """
    SELECT 
        UNE,
        UNE_NOME,
        SUM(VENDA_30DD) as total_vendas
    FROM read_parquet('data/parquet/admmat.parquet')
    WHERE PRODUTO = 369947
    GROUP BY UNE, UNE_NOME
    ORDER BY total_vendas DESC
    LIMIT 10
    """
    
    result = adapter.query(query)
    total = len(result)
    
    # Assert
    assert total == 10, f"Esperava 10 UNEs, recebeu {total}"
    
    # Verificar ordenação
    vendas = result['total_vendas'].tolist()
    assert vendas == sorted(vendas, reverse=True), "Deve estar ordenado DESC"
    
    print(f"✅ PASS: Top 10 UNEs retornadas corretamente")
    print(f"   Top 3: {vendas[:3]}")

if __name__ == "__main__":
    print("=== INTEGRATION TESTS: Dados Reais do Parquet ===\n")
    
    tests = [
        ("Produto 369947 tem 35 UNEs", test_produto_369947_tem_35_unes),
        ("LIMIT 100 retorna 100 registros", test_limite_100_retorna_100_registros),
        ("LIMIT 500 retorna 500 registros", test_limite_500_retorna_500_registros),
        ("Produto 369947 todas UNEs sem limite", test_produto_369947_todas_unes_sem_limite),
        ("Agregação top 10 UNEs", test_agregacao_top_10_unes),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n🧪 Teste: {name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"RESULTADOS: {passed} passaram, {failed} falharam")
    print(f"{'='*60}")
    
    if failed == 0:
        print("\n✅ TODOS OS INTEGRATION TESTS PASSARAM!")
        print("   Dados reais validados com sucesso!")
    else:
        print(f"\n❌ {failed} teste(s) falharam")
        exit(1)

    """
    DADO: Produto 369947 com 35 UNEs com vendas no banco real
    QUANDO: Consultar via consultar_dados_flexivel
    ENTÃO: Deve retornar todas as 35 UNEs
    """
    # Arrange
    from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
    
    # Act
    resultado = consultar_dados_flexivel.func(
        filtros={"PRODUTO": 369947},
        colunas=["UNE", "UNE_NOME", "VENDA_30DD", "ESTOQUE_UNE"],
        ordenar_por="VENDA_30DD",
        ordem_desc=True,
        limite=100
    )
    
    # Assert
    assert "total_resultados" in resultado, "Resultado deve conter 'total_resultados'"
    assert "resultados" in resultado, "Resultado deve conter 'resultados'"
    
    total = resultado["total_resultados"]
    assert total >= 35, f"❌ BUG: Esperava >= 35 UNEs, recebeu {total}"
    assert total <= 36, f"⚠️ Dados mudaram? Esperava ~35 UNEs, recebeu {total}"
    
    # Verificar estrutura dos dados
    assert len(resultado["resultados"]) == total
    primeiro_resultado = resultado["resultados"][0]
    assert "UNE" in primeiro_resultado
    assert "VENDA_30DD" in primeiro_resultado
    
    print(f"✅ PASS: Produto 369947 retornou {total} UNEs")
    print(f"   Top 3 UNEs por vendas:")
    for i, r in enumerate(resultado["resultados"][:3], 1):
        print(f"   {i}. UNE {r['UNE']}: {r['VENDA_30DD']} vendas")

@patch('backend.app.core.tools.flexible_query_tool.get_current_user_segments', return_value=["*"])
def test_limite_100_funciona_com_dados_reais(mock_rls):
    """
    DADO: Query sem filtro (muitos resultados)
    QUANDO: Usar limite padrão de 100
    ENTÃO: Deve retornar exatamente 100 resultados
    """
    # Arrange
    from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
    
    # Act
    resultado = consultar_dados_flexivel.func(
        filtros={},  # Sem filtro
        colunas=["UNE", "PRODUTO"],
        limite=100
    )
    
    # Assert
    total = resultado["total_resultados"]
    assert total == 100, f"Esperava exatamente 100 resultados, recebeu {total}"
    print(f"✅ PASS: Limite 100 retornou exatamente {total} resultados")

@patch('backend.app.core.tools.flexible_query_tool.get_current_user_segments', return_value=["*"])
def test_limite_500_maximo_com_dados_reais(mock_rls):
    """
    DADO: Query sem filtro com limite=1000
    QUANDO: Executar consulta
    ENTÃO: Deve ser cortado para 500 (máximo)
    """
    # Arrange
    from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
    
    # Act
    resultado = consultar_dados_flexivel.func(
        filtros={},
        colunas=["UNE", "PRODUTO"],
        limite=1000  # Acima do máximo
    )
    
    # Assert
    total = resultado["total_resultados"]
    assert total == 500, f"Esperava 500 (máximo), recebeu {total}"
    print(f"✅ PASS: Limite máximo de 500 aplicado corretamente ({total} resultados)")

@patch('backend.app.core.tools.flexible_query_tool.get_current_user_segments', return_value=["*"])
def test_agregacao_com_limite(mock_rls):
    """
    DADO: Query com agregação (soma de vendas por UNE)
    QUANDO: Usar limite de 10
    ENTÃO: Deve retornar top 10 UNEs por vendas
    """
    # Arrange
    from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
    
    # Act
    resultado = consultar_dados_flexivel.func(
        filtros={"PRODUTO": 369947},
        agregacao="soma",
        coluna_agregacao="VENDA_30DD",
        agrupar_por=["UNE", "UNE_NOME"],
        limite=10
    )
    
    # Assert
    total = resultado["total_resultados"]
    assert total == 10, f"Esperava 10 UNEs, recebeu {total}"
    
    # Verificar que está ordenado por valor (DESC)
    valores = [r["valor"] for r in resultado["resultados"]]
    assert valores == sorted(valores, reverse=True), "Resultados devem estar ordenados DESC"
    
    print(f"✅ PASS: Agregação retornou top {total} UNEs")
    print(f"   Top 3: {valores[:3]}")

@patch('backend.app.core.tools.flexible_query_tool.get_current_user_segments', return_value=["*"])
def test_comparacao_antes_depois_correcao(mock_rls):
    """
    DADO: Produto 369947 com 35 UNEs
    QUANDO: Consultar com limite padrão
    ENTÃO: Deve retornar TODAS as 35 UNEs (não apenas 9-20 como antes)
    """
    # Arrange
    from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
    from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
    
    # Verificar total real no banco
    adapter = get_duckdb_adapter()
    query_real = """
    SELECT COUNT(DISTINCT UNE) as total
    FROM read_parquet('data/parquet/admmat.parquet')
    WHERE PRODUTO = 369947 AND VENDA_30DD > 0
    """
    total_real = adapter.query(query_real)['total'][0]
    
    # Act - Consultar via ferramenta
    resultado = consultar_dados_flexivel.func(
        filtros={"PRODUTO": 369947},
        colunas=["UNE"],
        limite=100  # Padrão agora é 100
    )
    
    # Assert
    total_ferramenta = resultado["total_resultados"]
    
    # ANTES da correção: retornaria apenas 9-20 UNEs
    # DEPOIS da correção: deve retornar TODAS as 35 UNEs
    assert total_ferramenta == total_real, f"Ferramenta retornou {total_ferramenta}, mas banco tem {total_real}"
    assert total_ferramenta >= 35, f"Correção falhou: ainda retorna apenas {total_ferramenta} UNEs"
    
    print(f"✅ PASS: Correção validada!")
    print(f"   Banco real: {total_real} UNEs")
    print(f"   Ferramenta: {total_ferramenta} UNEs")
    print(f"   ANTES da correção: retornaria apenas ~9-20 UNEs")
    print(f"   DEPOIS da correção: retorna TODAS as {total_ferramenta} UNEs ✅")

if __name__ == "__main__":
    print("=== INTEGRATION TESTS: consultar_dados_flexivel (Dados Reais) ===\n")
    
    tests = [
        ("Produto 369947 retorna 35 UNEs", test_produto_369947_retorna_35_unes),
        ("Limite 100 funciona", test_limite_100_funciona_com_dados_reais),
        ("Limite máximo 500", test_limite_500_maximo_com_dados_reais),
        ("Agregação com limite", test_agregacao_com_limite),
        ("Comparação antes/depois correção", test_comparacao_antes_depois_correcao),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n🧪 Teste: {name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"RESULTADOS: {passed} passaram, {failed} falharam")
    print(f"{'='*60}")
    
    if failed == 0:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print(f"❌ {failed} teste(s) falharam")
        exit(1)
