"""
Test Suite: Chat BI Integration Tests
Metodologia: Test Engineer (AAA Pattern + Testing Pyramid)

Objetivo: Validar que o Chat BI funciona corretamente após correções de limitações.

Estrutura:
- Unit Tests: Componentes individuais (ChatServiceV3, _process_agent_response)
- Integration Tests: Fluxo completo (SSE stream, agent execution)
- E2E Tests: User flow completo (via Playwright - separado)
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Imports do sistema
import sys
sys.path.insert(0, 'app')

from app.services.chat_service_v3 import ChatServiceV3
from app.core.utils.session_manager import SessionManager


class TestChatServiceV3ProcessAgentResponse:
    """
    UNIT TESTS: _process_agent_response()
    
    Objetivo: Garantir que a extração de response_text funciona com todos os formatos possíveis.
    """
    
    def setup_method(self):
        """Arrange: Setup para cada teste"""
        self.session_manager = Mock(spec=SessionManager)
        self.service = ChatServiceV3(session_manager=self.session_manager)
    
    def test_extract_from_response_key(self):
        """
        TESTE 1: Extração de response_text da chave 'response' (formato padrão)
        
        Arrange: Resposta do agente com chave 'response'
        Act: Processar resposta
        Assert: response_text extraído corretamente
        """
        # Arrange
        agent_response = {
            "response": "Análise completa do produto 369947",
            "tool_calls": []
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["type"] == "text"
        assert result["result"]["mensagem"] == "Análise completa do produto 369947"
        assert "chart_data" not in result
    
    def test_extract_from_text_override(self):
        """
        TESTE 2: Extração de response_text da chave 'text_override' (fallback 1)
        """
        # Arrange
        agent_response = {
            "text_override": "Resposta alternativa",
            "tool_calls": []
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["result"]["mensagem"] == "Resposta alternativa"
    
    def test_extract_from_result_string(self):
        """
        TESTE 3: Extração de response_text da chave 'result' (quando é string)
        """
        # Arrange
        agent_response = {
            "result": "Resultado direto como string"
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["result"]["mensagem"] == "Resultado direto como string"
    
    def test_extract_from_result_dict_mensagem(self):
        """
        TESTE 4: Extração de response_text de 'result.mensagem' (dict aninhado)
        """
        # Arrange
        agent_response = {
            "result": {
                "mensagem": "Mensagem aninhada no dict",
                "other_data": "ignored"
            }
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["result"]["mensagem"] == "Mensagem aninhada no dict"
    
    def test_extract_from_mensagem_direct(self):
        """
        TESTE 5: Extração de response_text da chave 'mensagem' direta
        """
        # Arrange
        agent_response = {
            "mensagem": "Mensagem direta"
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["result"]["mensagem"] == "Mensagem direta"
    
    def test_fallback_when_empty(self):
        """
        TESTE 6: Fallback quando response_text está vazio
        
        CRÍTICO: Este é o bug que estamos corrigindo!
        """
        # Arrange
        agent_response = {
            "response": "",  # Vazio!
            "tool_calls": []
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["result"]["mensagem"] != ""  # NÃO deve ser vazio
        assert "não consegui gerar uma resposta" in result["result"]["mensagem"].lower()
    
    def test_fallback_when_whitespace_only(self):
        """
        TESTE 7: Fallback quando response_text é apenas espaços em branco
        """
        # Arrange
        agent_response = {
            "response": "   \n\t  "  # Apenas whitespace
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["result"]["mensagem"].strip() != ""
        assert "não consegui gerar uma resposta" in result["result"]["mensagem"].lower()
    
    def test_chart_data_extraction(self):
        """
        TESTE 8: Extração de chart_data quando presente
        """
        # Arrange
        chart_spec = {
            "type": "bar",
            "data": [{"x": "A", "y": 10}]
        }
        agent_response = {
            "response": "Gráfico gerado",
            "chart_data": chart_spec
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["result"]["mensagem"] == "Gráfico gerado"
        assert result["chart_data"] == chart_spec
    
    def test_chart_spec_fallback(self):
        """
        TESTE 9: Extração de chart_spec (nome alternativo)
        """
        # Arrange
        chart_spec = {"type": "line"}
        agent_response = {
            "response": "Linha de tendência",
            "chart_spec": chart_spec
        }
        
        # Act
        result = self.service._process_agent_response(agent_response)
        
        # Assert
        assert result["chart_data"] == chart_spec


class TestChatServiceV3Integration:
    """
    INTEGRATION TESTS: Fluxo completo do ChatServiceV3
    
    Objetivo: Validar que o serviço processa mensagens corretamente end-to-end.
    """
    
    @pytest.mark.asyncio
    async def test_process_message_success(self):
        """
        TESTE 10: Processamento completo de mensagem com sucesso
        
        Arrange: Mock do agente retornando resposta válida
        Act: Processar mensagem
        Assert: Resposta formatada corretamente
        """
        # Arrange
        session_manager = Mock(spec=SessionManager)
        session_manager.get_history.return_value = []
        session_manager.add_message = Mock()
        
        service = ChatServiceV3(session_manager=session_manager)
        
        # Mock do agente
        mock_agent_response = {
            "response": "Produto 369947 tem vendas em 35 UNEs",
            "tool_calls": ["consultar_dados_flexivel"]
        }
        
        with patch.object(service.agent, 'run_async', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_agent_response
            
            # Act
            result = await service.process_message(
                query="Vendas do produto 369947",
                session_id="test_session",
                user_id="test_user"
            )
            
            # Assert
            assert result["type"] == "text"
            assert "369947" in result["result"]["mensagem"]
            assert "35 UNEs" in result["result"]["mensagem"]
            
            # Verificar que histórico foi salvo
            assert session_manager.add_message.call_count == 2  # user + assistant


class TestChatEndpointSSE:
    """
    INTEGRATION TESTS: Endpoint SSE /chat/stream
    
    Objetivo: Validar que o endpoint SSE funciona corretamente.
    
    Nota: Estes testes requerem TestClient do FastAPI.
    """
    
    @pytest.mark.skip(reason="Requer setup completo do FastAPI app")
    def test_sse_stream_success(self):
        """
        TESTE 11: SSE stream retorna eventos corretamente
        
        TODO: Implementar com TestClient quando app estiver disponível
        """
        pass


# Executar testes
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
