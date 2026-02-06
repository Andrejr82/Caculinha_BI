"""
Script de teste para validar a arquitetura Metrics-First.

Testa todos os componentes principais:
1. QueryInterpreter
2. MetricsCalculator
3. MetricsValidator
4. ContextBuilder
5. ChatServiceV3 (integração)
"""

import sys
import asyncio
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app.services.query_interpreter import QueryInterpreter, NeedsClarificationError
from app.services.metrics_calculator import MetricsCalculator
from app.services.metrics_validator import validate_metrics, NoDataError, InvalidMetricError
from app.services.context_builder import ContextBuilder


def test_query_interpreter():
    """Testa o QueryInterpreter"""
    print("\n" + "="*60)
    print("TESTE 1: QueryInterpreter")
    print("="*60)
    
    interpreter = QueryInterpreter()
    
    # Teste 1.1: Query simples (heurística)
    print("\n[1.1] Query simples - 'vendas da loja 1685'")
    intent = interpreter.interpret("vendas da loja 1685")
    print(f"✅ Intent: {intent.intent_type}")
    print(f"✅ Confiança: {intent.confidence:.2f}")
    print(f"✅ Entidades: {intent.entities}")
    assert intent.intent_type == "vendas", "Intent type incorreto"
    assert intent.confidence >= 0.8, "Confiança muito baixa"
    assert intent.entities.get("une") == 1685, "UNE não extraída"
    
    # Teste 1.2: Query de estoque
    print("\n[1.2] Query de estoque - 'quanto tem em estoque de tecidos'")
    intent = interpreter.interpret("quanto tem em estoque de tecidos")
    print(f"✅ Intent: {intent.intent_type}")
    print(f"✅ Confiança: {intent.confidence:.2f}")
    print(f"✅ Entidades: {intent.entities}")
    assert intent.intent_type == "estoque", "Intent type incorreto"
    
    # Teste 1.3: Query de ruptura
    print("\n[1.3] Query de ruptura - 'produtos em ruptura'")
    intent = interpreter.interpret("produtos em ruptura")
    print(f"✅ Intent: {intent.intent_type}")
    print(f"✅ Confiança: {intent.confidence:.2f}")
    assert intent.intent_type == "ruptura", "Intent type incorreto"
    
    # Teste 1.4: Query ambígua (deve pedir esclarecimento)
    print("\n[1.4] Query ambígua - 'abc xyz 123'")
    try:
        intent = interpreter.interpret("abc xyz 123")
        print("❌ Deveria ter levantado NeedsClarificationError")
        assert False, "Não detectou query ambígua"
    except NeedsClarificationError as e:
        print(f"✅ NeedsClarificationError levantado: {str(e)[:50]}...")
    
    print("\n✅ QueryInterpreter: TODOS OS TESTES PASSARAM")


def test_metrics_calculator():
    """Testa o MetricsCalculator"""
    print("\n" + "="*60)
    print("TESTE 2: MetricsCalculator")
    print("="*60)
    
    calculator = MetricsCalculator()
    
    # Teste 2.1: Cálculo de vendas
    print("\n[2.1] Calcular vendas da loja 1685")
    metrics = calculator.calculate(
        intent_type="vendas",
        entities={"une": 1685},
        aggregations=["sum"]
    )
    print(f"✅ Linhas retornadas: {metrics.row_count}")
    print(f"✅ Tempo de execução: {metrics.execution_time_ms:.2f}ms")
    print(f"✅ Métricas: {list(metrics.metrics.keys())}")
    assert metrics.row_count > 0, "Nenhum dado retornado"
    assert "total_vendas" in metrics.metrics, "Métrica total_vendas não encontrada"
    
    # Teste 2.2: Cálculo de estoque
    print("\n[2.2] Calcular estoque de TECIDOS")
    metrics = calculator.calculate(
        intent_type="estoque",
        entities={"segmento": "TECIDOS"},
        aggregations=["sum"]
    )
    print(f"✅ Linhas retornadas: {metrics.row_count}")
    print(f"✅ Métricas: {metrics.metrics}")
    assert metrics.row_count > 0, "Nenhum dado retornado"
    
    # Teste 2.3: Cálculo de rupturas
    print("\n[2.3] Calcular rupturas")
    metrics = calculator.calculate(
        intent_type="ruptura",
        entities={},
        aggregations=["count"]
    )
    print(f"✅ Rupturas encontradas: {metrics.metrics.get('qtd_rupturas', 0)}")
    
    calculator.close()
    print("\n✅ MetricsCalculator: TODOS OS TESTES PASSARAM")


def test_metrics_validator():
    """Testa o MetricsValidator"""
    print("\n" + "="*60)
    print("TESTE 3: MetricsValidator (Truth Contract)")
    print("="*60)
    
    calculator = MetricsCalculator()
    
    # Teste 3.1: Validação com dados válidos
    print("\n[3.1] Validar métricas válidas")
    metrics = calculator.calculate(
        intent_type="vendas",
        entities={"une": 1685},
        aggregations=["sum"]
    )
    try:
        validate_metrics(metrics)
        print("✅ Métricas válidas aceitas")
    except Exception as e:
        print(f"❌ Validação falhou inesperadamente: {e}")
        assert False, "Validação falhou para métricas válidas"
    
    # Teste 3.2: Validação com dados vazios (deve levantar NoDataError)
    print("\n[3.2] Validar métricas vazias (produto inexistente)")
    metrics = calculator.calculate(
        intent_type="vendas",
        entities={"produto": 999999999},
        aggregations=["sum"]
    )
    try:
        validate_metrics(metrics)
        print("❌ Deveria ter levantado NoDataError")
        assert False, "Não detectou dados vazios"
    except NoDataError as e:
        print(f"✅ NoDataError levantado: {str(e)[:50]}...")
    
    calculator.close()
    print("\n✅ MetricsValidator: TODOS OS TESTES PASSARAM")


def test_context_builder():
    """Testa o ContextBuilder"""
    print("\n" + "="*60)
    print("TESTE 4: ContextBuilder")
    print("="*60)
    
    calculator = MetricsCalculator()
    interpreter = QueryInterpreter()
    builder = ContextBuilder()
    
    # Teste 4.1: Construir contexto para vendas
    print("\n[4.1] Construir contexto para vendas")
    intent = interpreter.interpret("vendas da loja 1685")
    metrics = calculator.calculate(
        intent_type=intent.intent_type,
        entities=intent.entities,
        aggregations=intent.aggregations
    )
    
    context = builder.build(metrics, intent)
    print(f"✅ Tokens estimados: {context.total_tokens}")
    print(f"✅ Resumo: {context.summary[:50]}...")
    print(f"✅ Tem tabela de detalhes: {context.details_table_md is not None}")
    
    # Verificar formato Markdown
    context_str = builder.to_string(context)
    assert "##" in context_str, "Faltam headers Markdown"
    assert "**" in context_str, "Faltam negrito Markdown"
    print(f"✅ Contexto Markdown válido ({len(context_str)} caracteres)")
    
    calculator.close()
    print("\n✅ ContextBuilder: TODOS OS TESTES PASSARAM")


async def test_chat_service_v3():
    """Testa o ChatServiceV3 (integração)"""
    print("\n" + "="*60)
    print("TESTE 5: ChatServiceV3 (Integração)")
    print("="*60)
    
    from app.core.utils.session_manager import SessionManager
    from app.services.chat_service_v3 import ChatServiceV3
    
    # Inicializar serviço
    print("\n[5.1] Inicializando ChatServiceV3...")
    session_manager = SessionManager(storage_dir="app/data/sessions")
    service = ChatServiceV3(session_manager=session_manager)
    print("✅ ChatServiceV3 inicializado")
    
    # Teste 5.2: Query simples
    print("\n[5.2] Processar query: 'vendas da loja 1685'")
    result = await service.process_message(
        query="vendas da loja 1685",
        session_id="test_session",
        user_id="test_user"
    )
    print(f"✅ Tipo de resposta: {result.get('type')}")
    print(f"✅ Tem mensagem: {'mensagem' in result.get('result', {})}")
    assert result.get("type") == "text", "Tipo de resposta incorreto"
    assert "mensagem" in result.get("result", {}), "Mensagem não encontrada"
    print(f"✅ Resposta: {result['result']['mensagem'][:100]}...")
    
    # Teste 5.3: Query sem dados (Truth Contract)
    print("\n[5.3] Processar query sem dados: 'vendas do produto 999999999'")
    result = await service.process_message(
        query="vendas do produto 999999999",
        session_id="test_session",
        user_id="test_user"
    )
    print(f"✅ Tipo de resposta: {result.get('response_type')}")
    assert result.get("system_response") == True, "Não é resposta do sistema"
    assert result.get("response_type") == "no_data", "Tipo de erro incorreto"
    print(f"✅ Mensagem do sistema: {result['result']['mensagem'][:80]}...")
    
    service.close()
    print("\n✅ ChatServiceV3: TODOS OS TESTES PASSARAM")


def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("INICIANDO TESTES DA ARQUITETURA METRICS-FIRST")
    print("="*60)
    
    try:
        # Testes síncronos
        test_query_interpreter()
        test_metrics_calculator()
        test_metrics_validator()
        test_context_builder()
        
        # Testes assíncronos
        asyncio.run(test_chat_service_v3())
        
        # Resumo final
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*60)
        print("\n📊 Resumo:")
        print("  ✅ QueryInterpreter: OK")
        print("  ✅ MetricsCalculator: OK")
        print("  ✅ MetricsValidator: OK")
        print("  ✅ ContextBuilder: OK")
        print("  ✅ ChatServiceV3: OK")
        print("\n🚀 Arquitetura Metrics-First está 100% funcional!")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
