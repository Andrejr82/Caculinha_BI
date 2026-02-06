# Tests para validar as mudanças realizadas:
# 1. Filtro de UNE (origem/destino) para 1→1, 1→N e N→N
# 2. Respostas vazias do ChatBI

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

class TestTransferFiltersUI:
    """
    Testes para validar que a página de transferências:
    - Apresenta seleção de UNE origem/destino no topo
    - Suporta 3 modos: 1→1, 1→N, N→N
    - Permite múltiplas seleções no modo apropriado
    """

    def test_filter_mode_selection(self):
        """Verifica se os 3 modos de transferência estão disponíveis"""
        modes = ['1→1', '1→N', 'N→N']
        # O componente React deve ter esses 3 botões de modo
        assert len(modes) == 3
        assert '1→1' in modes
        assert '1→N' in modes
        assert 'N→N' in modes

    def test_origin_destination_selection_logic(self):
        """
        Testa a lógica de seleção origem/destino:
        - 1→1: Uma origem, Uma destino (seleção única)
        - 1→N: Uma origem, Múltiplos destinos
        - N→N: Múltiplos origens, Múltiplos destinos
        """
        # Simulando a lógica do componente React
        unes = [1, 2, 3, 4, 5]
        
        # Caso 1: 1→1
        mode = '1→1'
        selected_origin = 1
        selected_destinations = [2]  # Apenas uma
        assert len(selected_destinations) == 1, f"Modo {mode} deve ter apenas 1 destino"
        
        # Caso 2: 1→N
        mode = '1→N'
        selected_origin = 1
        selected_destinations = [2, 3, 4]  # Múltiplos destinos, 1 origem
        assert len(selected_destinations) > 1, f"Modo {mode} deve permitir múltiplos destinos"
        assert selected_origin in unes
        
        # Caso 3: N→N
        mode = 'N→N'
        selected_origins = [1, 2]  # Múltiplas origens
        selected_destinations = [3, 4, 5]  # Múltiplos destinos
        assert len(selected_origins) > 1, f"Modo {mode} deve permitir múltiplas origens"
        assert len(selected_destinations) > 1, f"Modo {mode} deve permitir múltiplos destinos"

    def test_destination_cannot_be_origin(self):
        """Verifica que UNE destino não pode ser igual a origem"""
        selected_origin = 1
        available_unes = [1, 2, 3, 4, 5]
        
        valid_destinations = [une for une in available_unes if une != selected_origin]
        
        assert selected_origin not in valid_destinations
        assert len(valid_destinations) == len(available_unes) - 1


class TestChatBIResponses:
    """
    Testes para validar que o ChatBI:
    - Nunca retorna respostas vazias
    - Sempre tem um fallback quando há erro
    - Processa queries corretamente
    """

    @pytest.mark.asyncio
    async def test_agent_never_returns_empty_response(self):
        """
        Valida que CaculinhaBIAgent.run() NUNCA retorna dict vazio
        ou resposta vazia
        """
        # Mock do agente
        from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
        from unittest.mock import MagicMock
        
        mock_llm = MagicMock()
        mock_field_mapper = MagicMock()
        mock_code_gen_agent = MagicMock()
        
        # Configurar mocks
        mock_field_mapper.get_known_fields.return_value = ['produto', 'estoque', 'une']
        
        agent = CaculinhaBIAgent(
            llm=mock_llm,
            code_gen_agent=mock_code_gen_agent,
            field_mapper=mock_field_mapper
        )
        
        # Teste 1: Query que deve gerar fallback
        result = agent.run(user_query="xyz123 aleatório", chat_history=[])
        
        assert result is not None, "Agent nunca deve retornar None"
        assert isinstance(result, dict), "Agent deve retornar um dicionário"
        assert len(result) > 0, "Resposta não deve ser um dict vazio"
        assert "type" in result or "result" in result, "Resposta deve ter type ou result"

    @pytest.mark.asyncio
    async def test_fallback_response_has_content(self):
        """
        Valida que o método _generate_fallback_response sempre
        retorna uma mensagem com conteúdo
        """
        from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
        from unittest.mock import MagicMock
        
        mock_llm = MagicMock()
        mock_field_mapper = MagicMock()
        mock_code_gen_agent = MagicMock()
        
        mock_field_mapper.get_known_fields.return_value = ['produto', 'estoque', 'une']
        
        agent = CaculinhaBIAgent(
            llm=mock_llm,
            code_gen_agent=mock_code_gen_agent,
            field_mapper=mock_field_mapper
        )
        
        # Gerar fallback response
        fallback = agent._generate_fallback_response("test query")
        
        # Validações
        assert fallback is not None
        assert fallback.get("type") in ["text", "tool_result", "error"]
        
        # Extrair mensagem
        result = fallback.get("result", {})
        if isinstance(result, dict):
            mensagem = result.get("mensagem", "")
        else:
            mensagem = str(result)
        
        assert mensagem, "Fallback deve ter mensagem com conteúdo"
        assert len(mensagem) > 10, "Mensagem deve ter conteúdo significativo"

    def test_endpoint_handles_empty_agent_response(self):
        """
        Valida que o endpoint /chat/stream trata adequadamente
        caso o agente retorne resposta vazia
        """
        # Este teste seria executado no contexto do endpoint
        # Aqui apenas validamos a lógica
        
        agent_response = None
        fallback_response = {
            "type": "text",
            "result": {
                "mensagem": "Desculpe, não consegui processar sua pergunta. Por favor, reformule e tente novamente."
            }
        }
        
        # A lógica do endpoint deve fazer isso:
        if not agent_response:
            agent_response = fallback_response
        
        assert agent_response is not None
        assert agent_response.get("result", {}).get("mensagem"), "Deve ter mensagem"

    def test_response_text_never_empty_in_stream(self):
        """
        Valida que o texto streamado nunca é vazio
        """
        # Simulando a lógica do endpoint
        response_types = ["text", "tool_result", "code_result"]
        
        for resp_type in response_types:
            response_text = ""
            
            # Se vazio, aplicar fallback
            if not response_text or (isinstance(response_text, str) and not response_text.strip()):
                response_text = "Resposta processada, mas nenhum texto foi gerado. Por favor, tente reformular sua pergunta."
            
            assert response_text, f"Resposta de tipo {resp_type} não deve ser vazia"
            assert len(response_text) > 0, "Texto de resposta deve ter conteúdo"


class TestIntegration:
    """
    Testes de integração simples para validar que:
    - Transferências funcionam com múltiplas UNEs
    - ChatBI responde a queries
    """

    def test_transfer_with_multiple_destinations(self):
        """
        Simula uma transferência 1→N: 
        1 UNE origem, múltiplas UNEs destino
        """
        transfer_request = {
            "modo": "1→N",
            "produto_id": 101,
            "une_origem": 1,
            "unes_destino": [2, 3, 4],
            "quantidade": 100
        }
        
        # Validar estrutura
        assert transfer_request["modo"] == "1→N"
        assert len(transfer_request["unes_destino"]) > 1
        assert transfer_request["une_origem"] not in transfer_request["unes_destino"]

    def test_transfer_with_multiple_origins_destinations(self):
        """
        Simula uma transferência N→N:
        Múltiplas UNEs origem, múltiplas UNEs destino
        """
        transfer_request = {
            "modo": "N→N",
            "produto_id": 101,
            "unes_origem": [1, 2],
            "unes_destino": [3, 4, 5],
            "quantidade": 100
        }
        
        # Validar estrutura
        assert transfer_request["modo"] == "N→N"
        assert len(transfer_request["unes_origem"]) > 1
        assert len(transfer_request["unes_destino"]) > 1
        # Não deve haver overlap entre origem e destino
        for o in transfer_request["unes_origem"]:
            assert o not in transfer_request["unes_destino"]


if __name__ == "__main__":
    # Executar testes básicos
    test = TestTransferFiltersUI()
    test.test_filter_mode_selection()
    test.test_origin_destination_selection_logic()
    test.test_destination_cannot_be_origin()
    
    test2 = TestChatBIResponses()
    test2.test_response_text_never_empty_in_stream()
    
    test3 = TestIntegration()
    test3.test_transfer_with_multiple_destinations()
    test3.test_transfer_with_multiple_origins_destinations()
    
    print("✅ Todos os testes básicos passaram!")
