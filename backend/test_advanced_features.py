"""
Teste das funcionalidades avançadas LLM - Fase 3.

Testa:
1. Self-Reflection
2. Structured Output (preparação)
3. Integração com ChatServiceV3
"""

import pytest
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))


def test_self_reflection_module_exists():
    """Verifica se módulo Self-Reflection foi criado"""
    from app.services.self_reflection import SelfReflection
    
    assert SelfReflection is not None
    print("✅ Módulo Self-Reflection criado")


def test_self_reflection_initialization():
    """Testa inicialização do Self-Reflection"""
    from app.services.self_reflection import SelfReflection
    from app.core.llm_factory import LLMFactory
    
    llm = LLMFactory.get_adapter(use_smart=False)
    reflector = SelfReflection(llm)
    
    assert reflector.llm is not None
    print("✅ Self-Reflection inicializado corretamente")


def test_chat_service_has_reflection_method():
    """Verifica se ChatServiceV3 tem método _should_use_reflection"""
    from app.services.chat_service_v3 import ChatServiceV3
    
    assert hasattr(ChatServiceV3, '_should_use_reflection')
    print("✅ ChatServiceV3 tem método _should_use_reflection")


def test_should_use_reflection_logic():
    """Testa lógica de decisão de usar reflection"""
    from app.services.chat_service_v3 import ChatServiceV3
    from app.core.utils.session_manager import SessionManager
    from app.services.query_interpreter import QueryIntent, IntentType
    
    session_manager = SessionManager(storage_dir="app/data/sessions")
    service = ChatServiceV3(session_manager=session_manager)
    
    # Teste 1: Resposta curta não deve usar reflection
    short_narrative = "Resposta curta"
    intent_simple = QueryIntent(
        intent_type=IntentType.CHAT,
        entities={},
        aggregations=[],
        visualization=None,
        confidence=0.9,
        raw_query="teste"
    )
    
    # Pode ou não usar (aleatório para intents simples)
    result = service._should_use_reflection(short_narrative, intent_simple)
    assert isinstance(result, bool)
    print(f"✅ Resposta curta: reflection={result}")
    
    # Teste 2: Resposta longa deve usar reflection
    long_narrative = "x" * 600  # >500 chars
    result = service._should_use_reflection(long_narrative, intent_simple)
    assert result == True
    print("✅ Resposta longa: reflection=True")
    
    service.close()


def test_self_reflection_critique_format():
    """Verifica estrutura do prompt de crítica"""
    import inspect
    from app.services.self_reflection import SelfReflection
    
    source = inspect.getsource(SelfReflection._generate_critique)
    
    # Verificar elementos do prompt de crítica
    assert "Clareza" in source
    assert "Precisão" in source
    assert "Insights" in source
    assert "Estrutura" in source
    assert "Completude" in source
    assert "APROVADO" in source or "REFINAR" in source
    
    print("✅ Prompt de crítica bem estruturado (5 critérios)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTES DAS FUNCIONALIDADES AVANÇADAS - FASE 3")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])
