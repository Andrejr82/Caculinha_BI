import pytest
import asyncio
from app.services.chat_service_v3 import ChatServiceV3
from app.core.utils.session_manager import SessionManager
from app.services.query_interpreter import IntentType

# Mock LLM to avoid API calls during integration tests
class MockLLMAdapter:
    def __init__(self, *args, **kwargs):
        pass
        
    def generate_with_history(self, *args, **kwargs):
        return "Narrativa gerada pelo Mock"

@pytest.fixture
def chat_service(monkeypatch):
    # Mock LLM Factory to return our Mock adapter
    # But we want REAL QueryInterpreter and REAL MetricsCalculator
    # QueryInterpreter uses LLM only for fallback (20%), so we might need a smart mock there if we test complex queries.
    # For now, let's test the "Happy Path" heuristics which don't use LLM.
    
    # We patch the _generate_narrative method to avoid the LLM call for the final text
    # allowing us to inspect the intermediate steps if we exposed them, 
    # but ChatServiceV3 encapsulates everything.
    
    # Better strategy: Test the components individually in integration
    pass

@pytest.mark.asyncio
async def test_metrics_calculation_vendas_global():
    """Testa se o cálculo de vendas global retorna números coerentes"""
    from app.services.metrics_calculator import MetricsCalculator
    
    calc = MetricsCalculator() # Uses real admmat.parquet by default
    
    result = calc.calculate(
        intent_type="vendas",
        entities={"periodo": "30d"},
        aggregations=["sum"]
    )
    
    assert result.row_count > 0
    assert result.metrics["total_vendas"] > 0
    assert "total_vendas" in result.metrics
    assert result.execution_time_ms > 0

@pytest.mark.asyncio
async def test_metrics_calculation_loja_especifica():
    """Testa filtro de loja específica"""
    from app.services.metrics_calculator import MetricsCalculator
    calc = MetricsCalculator()
    
    # Loja 2586 (sabemos que existe do teste anterior)
    result = calc.calculate(
        intent_type="vendas",
        entities={"une": 2586, "periodo": "30d"},
        aggregations=["sum"]
    )
    
    assert result.row_count > 0
    assert result.metrics["total_vendas"] > 0
    # A venda da loja deve ser menor que a venda global
    # (Este teste assume que a base tem mais de uma loja)

@pytest.mark.asyncio
async def test_metrics_calculation_top_segmentos():
    """Testa se os segmentos são calculados mesmo em intent VENDAS"""
    from app.services.metrics_calculator import MetricsCalculator
    calc = MetricsCalculator()
    
    result = calc.calculate(
        intent_type="vendas",
        entities={"periodo": "30d"},
        aggregations=["sum"]
    )
    
    # Verifica se a lista de segmentos foi populada (nossa correção)
    assert hasattr(result, "segments")
    assert len(result.segments) > 0
    assert "segmento" in result.segments[0]
    assert "vendas" in result.segments[0]

@pytest.mark.asyncio
async def test_context_builder_includes_segments():
    """Testa se o ContextBuilder inclui a tabela de segmentos no Markdown"""
    from app.services.context_builder import ContextBuilder
    from app.services.metrics_calculator import MetricsResult
    from app.services.query_interpreter import QueryIntent, IntentType
    
    builder = ContextBuilder()
    
    # Mock data
    metrics_result = MetricsResult(
        metrics={"total_vendas": 1000.0},
        dimensions=[],
        segments=[
            {"segmento": "TESTE_SEG", "vendas": 500.0},
            {"segmento": "OUTRO", "vendas": 500.0}
        ],
        metadata={}
    )
    
    intent = QueryIntent(
        intent_type=IntentType.VENDAS,
        entities={},
        aggregations=[],
        visualization=None,
        confidence=1.0,
        raw_query="teste"
    )
    
    context = builder.build(metrics_result, intent)
    
    assert "Top Segmentos" in context.summary or "Top Segmentos" in context.details_table_md
    assert "| TESTE_SEG | R$ 500.00 |" in context.details_table_md

