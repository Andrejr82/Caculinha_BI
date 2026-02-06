"""
Teste das melhorias de prompts implementadas.

Testa:
1. QueryInterpreter melhorado (Few-Shot + CoT)
2. Remoção de prompts obsoletos
3. Qualidade de classificação
"""

import pytest
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))


def test_obsolete_prompts_removed():
    """Verifica se prompts obsoletos foram removidos"""
    import os
    
    # master_prompt.py deve ter sido removido
    master_prompt_path = Path("app/core/agents/master_prompt.py")
    assert not master_prompt_path.exists(), "master_prompt.py ainda existe! Deveria ter sido removido"
    
    # graph/agent.py deve ter sido removido
    graph_agent_path = Path("app/core/graph/agent.py")
    assert not graph_agent_path.exists(), "graph/agent.py ainda existe! Deveria ter sido removido"
    
    print("✅ Prompts obsoletos removidos com sucesso")


def test_query_interpreter_improved():
    """Testa QueryInterpreter melhorado com Few-Shot + CoT"""
    from app.services.query_interpreter import QueryInterpreter
    
    # Criar interpreter sem LLM (testar apenas heurística)
    interpreter = QueryInterpreter(llm_adapter=None)
    
    # Teste 1: Query clara de vendas
    intent = interpreter.interpret("vendas da loja 1685")
    assert intent.intent_type.value == "vendas"
    assert intent.confidence >= 0.85
    assert intent.entities.get("une") == 1685
    print(f"✅ Query vendas: {intent.intent_type} (confiança: {intent.confidence:.2f})")
    
    # Teste 2: Query de estoque
    intent = interpreter.interpret("quanto tem em estoque de tecidos")
    assert intent.intent_type.value == "estoque"
    assert intent.entities.get("segmento") == "TECIDOS"
    print(f"✅ Query estoque: {intent.intent_type} (confiança: {intent.confidence:.2f})")
    
    # Teste 3: Query de gráfico
    intent = interpreter.interpret("mostre um gráfico de rupturas")
    assert intent.intent_type.value in ["ruptura", "grafico"]
    assert intent.visualization == "auto"
    print(f"✅ Query gráfico: {intent.intent_type} (confiança: {intent.confidence:.2f})")


def test_query_interpreter_prompt_quality():
    """Verifica qualidade do novo prompt"""
    import inspect
    from app.services.query_interpreter import QueryInterpreter
    
    # Obter código fonte do método _llm_classify
    source = inspect.getsource(QueryInterpreter._llm_classify)
    
    # Verificar elementos do prompt melhorado
    assert "CHAIN-OF-THOUGHT" in source or "Raciocínio" in source
    assert "FEW-SHOT" in source or "EXEMPLOS" in source
    assert "Exemplo 1" in source or "Example 1" in source
    
    # Contar exemplos (deve ter pelo menos 3)
    example_count = source.count("Exemplo")
    assert example_count >= 3, f"Prompt deve ter pelo menos 3 exemplos, encontrados: {example_count}"
    
    print(f"✅ Prompt melhorado com {example_count} exemplos Few-Shot")


def test_prompt_structure():
    """Testa estrutura do prompt melhorado"""
    from app.services.query_interpreter import QueryInterpreter
    import inspect
    
    source = inspect.getsource(QueryInterpreter._llm_classify)
    
    # Verificar seções do prompt
    assert "Raciocínio" in source, "Falta seção de raciocínio (CoT)"
    assert "Intenção" in source, "Falta análise de intenção"
    assert "Confiança" in source, "Falta análise de confiança"
    assert "JSON" in source, "Falta formato de saída JSON"
    
    print("✅ Estrutura do prompt validada (CoT + Few-Shot + Structured Output)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTES DAS MELHORIAS DE PROMPTS")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])
