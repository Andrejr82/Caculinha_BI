"""
Unit Tests: consultar_dados_flexivel - Comportamento de Limites
Seguindo AAA Pattern (Arrange, Act, Assert)
"""
import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

def test_limite_padrao_e_100():
    """
    DADO: Verificar valor padrão do parâmetro limite
    QUANDO: Inspecionar código da função
    ENTÃO: Deve ser 100
    """
    # Arrange & Act
    from app.core.tools import flexible_query_tool
    import inspect
    
    # A ferramenta é um StructuredTool, precisamos acessar a função real
    tool = flexible_query_tool.consultar_dados_flexivel
    
    # Se for StructuredTool, acessar func
    if hasattr(tool, 'func'):
        func = tool.func
    else:
        func = tool
    
    # Obter assinatura da função real
    sig = inspect.signature(func)
    limite_param = sig.parameters['limite']
    
    # Assert
    assert limite_param.default == 100, f"Limite padrão deveria ser 100, mas é {limite_param.default}"
    print("✅ PASS: Limite padrão é 100")


def test_limite_maximo_e_500():
    """
    DADO: Código da função consultar_dados_flexivel
    QUANDO: Verificar lógica de limite máximo
    ENTÃO: Deve cortar em 500
    """
    # Arrange & Act
    from app.core.tools import flexible_query_tool
    import inspect
    
    # Acessar função real
    tool = flexible_query_tool.consultar_dados_flexivel
    func = tool.func if hasattr(tool, 'func') else tool
    
    # Obter código fonte
    source = inspect.getsource(func)
    
    # Assert
    assert "if limite > 500:" in source, "Limite máximo deveria ser 500"
    assert "limite = 500" in source, "Deve ajustar para 500 quando exceder"
    print("✅ PASS: Limite máximo é 500")


def test_conversao_string_para_int():
    """
    DADO: Código da função
    QUANDO: Verificar lógica de conversão de string
    ENTÃO: Deve converter limite string para int
    """
    # Arrange & Act
    from app.core.tools import flexible_query_tool
    import inspect
    
    tool = flexible_query_tool.consultar_dados_flexivel
    func = tool.func if hasattr(tool, 'func') else tool
    source = inspect.getsource(func)
    
    # Assert
    assert "isinstance(limite, str)" in source, "Deve verificar se limite é string"
    assert "int(limite)" in source, "Deve converter string para int"
    print("✅ PASS: Conversão de string para int implementada")

def test_produto_369947_dados_reais():
    """
    DADO: Produto 369947 no banco de dados
    QUANDO: Consultar quantas UNEs têm o produto
    ENTÃO: Deve retornar ~35 UNEs
    """
    # Arrange
    from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
    
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
    assert total_unes <= 40, f"Esperava <= 40 UNEs, encontrou {total_unes}"
    print(f"✅ PASS: Produto 369947 tem {total_unes} UNEs com vendas")

def test_limite_antigo_removido():
    """
    DADO: Código da função
    QUANDO: Verificar se limite antigo de 50 foi removido
    ENTÃO: NÃO deve conter "if limite > 50"
    """
    # Arrange & Act
    from app.core.tools import flexible_query_tool
    import inspect
    
    tool = flexible_query_tool.consultar_dados_flexivel
    func = tool.func if hasattr(tool, 'func') else tool
    source = inspect.getsource(func)
    
    # Assert
    assert "if limite > 50:" not in source, "❌ Limite antigo de 50 ainda presente!"
    print("✅ PASS: Limite antigo de 50 foi removido")

if __name__ == "__main__":
    print("=== UNIT TESTS: consultar_dados_flexivel ===\n")
    
    try:
        test_limite_padrao_e_100()
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
    
    try:
        test_limite_maximo_e_500()
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
    
    try:
        test_conversao_string_para_int()
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
    
    try:
        test_produto_369947_dados_reais()
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
    
    try:
        test_limite_antigo_removido()
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
    
    print("\n=== TESTES CONCLUÍDOS ===")

