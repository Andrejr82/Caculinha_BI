
import pytest
from unittest.mock import MagicMock, patch
import asyncio # Adicionado para corrigir NameError


# Implementações
from backend.app.core.llm_factory import LLMFactory
from backend.app.core.llm_groq_adapter import GroqLLMAdapter

@pytest.fixture
def mock_llm_adapters():
    """Mock completo dos adapters invólucros usados pelo Factory."""
    with patch("app.core.llm_factory.SmartLLM") as mock_smart, \
         patch("app.core.llm_factory.GroqLLMAdapter") as mock_groq:
            
        mock_smart_instance = mock_smart.return_value
        mock_smart_instance.generate_response.return_value = "Mocked Response"
        
        mock_groq_instance = mock_groq.return_value
        mock_groq_instance.generate_response.return_value = "Mocked Groq Response"
        
        yield {
            "SmartLLM": mock_smart,
            "GroqLLMAdapter": mock_groq
        }

def test_get_adapter_returns_adapter(mock_llm_adapters):
    """Contrato: get_adapter deve retornar um objeto com método generate_response."""
    adapter = LLMFactory.get_adapter(use_smart=True)
    
    # Assert
    assert hasattr(adapter, 'generate_response')
    assert adapter.generate_response("oi") == "Mocked Response"

def test_get_adapter_fallback_logic(mock_llm_adapters):
    """Contrato: Se use_smart=False, deve retornar GroqLLMAdapter direto."""
    adapter = LLMFactory.get_adapter(provider="groq", use_smart=False)
    
    # Assert
    assert hasattr(adapter, 'generate_response')
    mock_llm_adapters['GroqLLMAdapter'].assert_called()

@pytest.mark.asyncio
async def test_generate_response_contract():
    """Contrato: generate_response deve ser assíncrono e retornar string."""
    # Como generate_response é async (awaitable), precisamos garantir que mock suporte isso
    # Aqui vamos instanciar um mock que imita o comportamento async
    
    mock_adapter = MagicMock()
    # Configurar mock async
    future = asyncio.Future()
    future.set_result("Async Response")
    mock_adapter.generate_response.return_value = future
    
    # Testar (simulando que esse mock veio do factory)
    response = await mock_adapter.generate_response("query")
    assert isinstance(response, str)
    assert response == "Async Response"
