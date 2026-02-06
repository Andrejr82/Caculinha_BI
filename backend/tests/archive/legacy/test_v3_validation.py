"""
Teste de Validação da Arquitetura Metrics-First V3.

Testa os componentes principais:
1. QueryInterpreter
2. MetricsCalculator  
3. MetricsValidator
4. ContextBuilder
5. ChatServiceV3

Execução: python -m pytest test_v3_validation.py -v
"""

import pytest
import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))


def test_imports():
    """Testa se todos os componentes V3 podem ser importados"""
    try:
        from app.services.query_interpreter import QueryInterpreter
        from app.services.metrics_calculator import MetricsCalculator
        from app.services.metrics_validator import validate_metrics
        from app.services.context_builder import ContextBuilder
        from app.services.chat_service_v3 import ChatServiceV3
        
        print("✅ Todos os imports V3 bem-sucedidos")
        assert True
    except ImportError as e:
        pytest.fail(f"Falha ao importar componentes V3: {e}")


def test_no_v2_imports():
    """Verifica que não há imports de V2 no código"""
    import subprocess
    
    # Verificar se chat_service_v2 não existe mais
    result = subprocess.run(
        ["python", "-c", "from app.services.chat_service_v2 import ChatServiceV2"],
        cwd=backend_path,
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0, "ChatServiceV2 ainda existe! Deveria ter sido removido"
    print("✅ ChatServiceV2 não encontrado (correto)")


def test_query_interpreter_basic():
    """Testa QueryInterpreter básico"""
    from app.services.query_interpreter import QueryInterpreter
    
    interpreter = QueryInterpreter()
    
    # Teste heurística simples
    intent = interpreter.interpret("vendas da loja 1685")
    
    assert intent.intent_type == "vendas", f"Intent incorreto: {intent.intent_type}"
    assert intent.confidence >= 0.7, f"Confiança muito baixa: {intent.confidence}"
    assert "une" in intent.entities or "loja" in str(intent.entities).lower()
    
    print(f"✅ QueryInterpreter funcionando: {intent.intent_type} (confiança: {intent.confidence:.2f})")


def test_metrics_calculator_initialization():
    """Testa inicialização do MetricsCalculator"""
    from app.services.metrics_calculator import MetricsCalculator
    
    calculator = MetricsCalculator()
    
    assert calculator.conn is not None, "Conexão DuckDB não inicializada"
    assert calculator.parquet_path.exists(), f"Parquet não encontrado: {calculator.parquet_path}"
    
    calculator.close()
    print("✅ MetricsCalculator inicializado corretamente")


def test_metrics_validator():
    """Testa MetricsValidator"""
    from app.services.metrics_validator import validate_metrics, NoDataError
    from app.services.metrics_calculator import MetricsResult
    
    # Teste com dados válidos
    valid_metrics = MetricsResult(
        metrics={"total": 100.0, "count": 10},
        dimensions=[],
        metadata={},
        row_count=10,
        execution_time_ms=50.0,
        cache_hit=False,
        query_sql="SELECT 1"
    )
    
    try:
        validate_metrics(valid_metrics)
        print("✅ MetricsValidator aceita métricas válidas")
    except Exception as e:
        pytest.fail(f"Validação falhou para métricas válidas: {e}")
    
    # Teste com dados vazios
    empty_metrics = MetricsResult(
        metrics={},
        dimensions=[],
        metadata={},
        row_count=0,
        execution_time_ms=10.0,
        cache_hit=False,
        query_sql="SELECT 1"
    )
    
    with pytest.raises(NoDataError):
        validate_metrics(empty_metrics)
    
    print("✅ MetricsValidator rejeita dados vazios (correto)")


def test_context_builder():
    """Testa ContextBuilder"""
    from app.services.context_builder import ContextBuilder
    from app.services.metrics_calculator import MetricsResult
    from app.services.query_interpreter import QueryIntent, IntentType
    
    builder = ContextBuilder()
    
    # Criar métricas de teste
    metrics = MetricsResult(
        metrics={"total_vendas": 1000.0, "qtd_produtos": 5},
        dimensions=[
            {"produto": "Produto A", "vendas": 500.0},
            {"produto": "Produto B", "vendas": 300.0}
        ],
        metadata={"periodo": "30d"},
        row_count=2,
        execution_time_ms=100.0,
        cache_hit=False,
        query_sql="SELECT ..."
    )
    
    # Criar intent de teste
    intent = QueryIntent(
        intent_type=IntentType.VENDAS,
        entities={"une": 1685},
        aggregations=["sum"],
        visualization=None,
        confidence=0.9,
        raw_query="vendas da loja 1685"
    )
    
    # Construir contexto
    context = builder.build(metrics, intent)
    
    assert context.summary, "Summary vazio"
    assert context.key_metrics_md, "Métricas vazias"
    assert context.total_tokens > 0, "Tokens não estimados"
    
    # Converter para string
    context_str = builder.to_string(context)
    assert "##" in context_str, "Faltam headers Markdown"
    assert "**" in context_str, "Faltam negrito Markdown"
    
    print(f"✅ ContextBuilder funcionando (~{context.total_tokens} tokens)")


def test_chat_service_v3_initialization():
    """Testa inicialização do ChatServiceV3"""
    from app.services.chat_service_v3 import ChatServiceV3
    from app.core.utils.session_manager import SessionManager
    
    session_manager = SessionManager(storage_dir="app/data/sessions")
    service = ChatServiceV3(session_manager=session_manager)
    
    assert service.query_interpreter is not None
    assert service.metrics_calculator is not None
    assert service.context_builder is not None
    
    service.close()
    print("✅ ChatServiceV3 inicializado corretamente")


def test_system_health():
    """Testa saúde geral do sistema"""
    import os
    
    # Verificar variáveis de ambiente críticas
    assert os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY não configurada"
    assert os.getenv("USE_SUPABASE_AUTH"), "USE_SUPABASE_AUTH não configurada"
    
    # Verificar arquivos críticos
    parquet_path = Path("data/parquet/admmat.parquet")
    assert parquet_path.exists(), f"Parquet não encontrado: {parquet_path}"
    
    print("✅ Sistema saudável")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTES DE VALIDAÇÃO - ARQUITETURA METRICS-FIRST V3")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])
