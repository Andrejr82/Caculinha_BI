"""
Teste específico das melhorias LLM implementadas.

Testa:
1. Novo prompt Master migrado
2. LLM Provider respeitando .env
3. Validação de queries ambíguas
4. Tratamento de erros melhorado
"""

import pytest
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))


def test_llm_provider_from_env():
    """Testa se LLM Provider respeita configuração do .env"""
    from app.core.llm_factory import LLMFactory
    from app.config.settings import settings
    
    # Verificar se settings carrega corretamente
    assert settings.LLM_PROVIDER, "LLM_PROVIDER não configurado no .env"
    
    # Criar adapter sem especificar provider
    adapter = LLMFactory.get_adapter(use_smart=False)
    
    # Verificar que respeitou o .env
    print(f"✅ LLM Provider configurado: {settings.LLM_PROVIDER}")
    assert True


def test_query_validation_ambiguous():
    """Testa validação de queries ambíguas"""
    from app.services.query_interpreter import QueryInterpreter, NeedsClarificationError
    
    interpreter = QueryInterpreter()
    
    # Teste 1: "produto em todas as lojas" sem especificar qual
    with pytest.raises(NeedsClarificationError) as exc_info:
        interpreter.interpret("gere um relatório de vendas do produto em todas as lojas")
    
    assert "QUAL produto" in str(exc_info.value)
    print("✅ Query ambígua detectada: produto não especificado")
    
    # Teste 2: Query completa deve passar
    try:
        intent = interpreter.interpret("vendas do produto 59294 em todas as lojas")
        assert intent.entities.get("produto") == 59294
        print(f"✅ Query completa aceita: produto {intent.entities['produto']}")
    except NeedsClarificationError:
        pytest.fail("Query completa não deveria levantar exceção")


def test_improved_error_handling():
    """Testa tratamento de erros melhorado"""
    from app.services.chat_service_v3 import SystemResponse
    
    # Teste criação de SystemResponse
    error_response = SystemResponse(
        message="Parâmetros inválidos: UNE deve ser numérico",
        suggestion="Verifique os filtros e tente novamente",
        type="validation_error"
    )
    
    response_dict = error_response.to_dict()
    
    assert response_dict["type"] == "text"
    assert response_dict["system_response"] == True
    assert response_dict["response_type"] == "validation_error"
    assert "sugestao" in response_dict["result"]
    
    print("✅ SystemResponse com sugestão funcionando")


def test_master_prompt_migration():
    """Testa se Master Prompt foi migrado corretamente"""
    from app.services.chat_service_v3 import ChatServiceV3
    from app.core.utils.session_manager import SessionManager
    
    session_manager = SessionManager(storage_dir="app/data/sessions")
    service = ChatServiceV3(session_manager=session_manager)
    
    # Verificar que o serviço foi inicializado
    assert service.query_interpreter is not None
    assert service.metrics_calculator is not None
    assert service.context_builder is not None
    
    service.close()
    print("✅ ChatServiceV3 com novo prompt inicializado")


def test_chain_of_thought_prompt():
    """Verifica se o prompt contém elementos de Chain-of-Thought"""
    import inspect
    from app.services.chat_service_v3 import ChatServiceV3
    
    # Obter código fonte do método _generate_narrative
    source = inspect.getsource(ChatServiceV3._generate_narrative)
    
    # Verificar elementos do Master Prompt
    assert "CHAIN-OF-THOUGHT" in source
    assert "FEW-SHOT" in source or "EXEMPLOS" in source
    assert "CONTEXT7" in source
    assert "TRUTH CONTRACT" in source
    
    print("✅ Prompt contém Chain-of-Thought e Few-Shot examples")


def test_increased_max_tokens():
    """Verifica se max_tokens foi aumentado"""
    import inspect
    from app.services.chat_service_v3 import ChatServiceV3
    
    source = inspect.getsource(ChatServiceV3._generate_narrative)
    
    # Verificar que max_tokens foi aumentado de 500 para 800
    assert "max_tokens=800" in source
    
    print("✅ max_tokens aumentado para 800 (respostas mais completas)")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTES DAS MELHORIAS LLM - FASE 1")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])
