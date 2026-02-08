
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import types
from unittest.mock import MagicMock

# MOCK ROBUSTO DE DEPENDÊNCIAS PESADAS
# Evita erro de DLL no Windows e 'torch.__spec__ is not set'
def mock_module(module_name):
    mod = types.ModuleType(module_name)
    mod.__spec__ = MagicMock()
    mod.__loader__ = MagicMock()
    mod.__file__ = "mocked_file.py"
    mod.__path__ = []
    sys.modules[module_name] = mod
    return mod

# Lista de módulos para mockar ANTES de qualquer import do app
modules_to_mock = [
    "torch", 
    "torch.nn",
    "shapely", 
    "shapely.geometry", 
    "sentence_transformers",
    "transformers", # Importante: transformers tenta importar torch
    "langchain_huggingface",
    # "numpy", # Removido
    # "pandas", # Removido
    # "polars", # Removido
    # "pyarrow", # Removido
]

# Aplicar mocks
for mod_name in modules_to_mock:
    # Apenas se não estiver carregado (ou forçar se quiser garantir)
    if mod_name not in sys.modules:
        mock_module(mod_name)

# Manter mocks globais acessíveis se precisar configurar retornos
sys.modules["torch"].Tensor = MagicMock()

import asyncio


# Componente principal a ser testado

# Vamos testar o ChatServiceV3 pois ele orquestra o pipeline
from backend.app.services.chat_service_v3 import ChatServiceV3

@pytest.fixture
def mock_dependencies():
    """Mock de todas as dependências externas do pipeline."""
    with patch("app.services.chat_service_v3.SessionManager") as mock_session, \
         patch("app.services.chat_service_v3.LLMFactory") as mock_llm_factory, \
         patch("app.services.chat_service_v3.CaculinhaBIAgent") as mock_agent_cls:
        
        # Mock Session Manager
        session_instance = mock_session.return_value
        session_instance.get_history.return_value = []
        
        # Mock LLM Adapter
        mock_llm = MagicMock()
        mock_llm_factory.get_adapter.return_value = mock_llm
        
        # Mock Agent
        agent_instance = mock_agent_cls.return_value
        # run_async deve ser awaitable
        agent_instance.run_async = AsyncMock()
        agent_instance.run_async.return_value = {
            "response": "Resposta processada pelo agente",
            "tool_calls": [{"name": "search", "args": {"q": "teste"}}],
            "chart_data": None
        }
        
        yield {
            "session": session_instance,
            "llm": mock_llm,
            "agent_cls": mock_agent_cls,
            "agent": agent_instance
        }

@pytest.mark.asyncio
async def test_cognitive_pipeline_end_to_end(mock_dependencies):
    """
    Simula um fluxo completo de ponta a ponta (controlado).
    UserInput -> ChatService -> SessionManager -> Agent -> LLM Protocol -> Output
    """
    deps = mock_dependencies
    
    # Setup Service
    service = ChatServiceV3(session_manager=deps['session'])
    
    # Act
    query = "Como estão as vendas?"
    response = await service.process_message(
        query=query,
        session_id="sess_123",
        user_id="user_456"
    )
    
    # Assert
    # 1. Serviço instanciou o agente corretamente
    deps['agent_cls'].assert_called_once()
    
    # 2. Serviço buscou histórico
    deps['session'].get_history.assert_called_with("sess_123", "user_456")
    
    # 3. Serviço chamou o agente
    deps['agent'].run_async.assert_called_once()
    call_args = deps['agent'].run_async.call_args
    assert call_args[0][0] == query # Primeiro arg é a query
    
    # 4. Serviço salvou histórico (User + Assistant)
    assert deps['session'].add_message.call_count == 2
    deps['session'].add_message.assert_any_call("sess_123", "user", query, "user_456")
    deps['session'].add_message.assert_any_call("sess_123", "assistant", "Resposta processada pelo agente", "user_456")
    
    # 5. Resposta final está no formato de API esperado
    assert response["type"] == "text"
    assert response["result"]["mensagem"] == "Resposta processada pelo agente"

@pytest.mark.asyncio
async def test_pipeline_handles_agent_error(mock_dependencies):
    """Valida resiliência do pipeline a falhas no agente."""
    deps = mock_dependencies
    
    # Simular erro no agente
    deps['agent'].run_async.side_effect = Exception("Erro interno no LLM")
    
    service = ChatServiceV3(session_manager=deps['session'])
    
    response = await service.process_message("query", "sess_1", "user_1")
    
    # Deve retornar mensagem de erro amigável, não explodir
    assert response["type"] == "text"
    assert "Erro ao processar" in response["result"]["mensagem"]
    assert "Erro interno no LLM" in response["result"]["mensagem"]
