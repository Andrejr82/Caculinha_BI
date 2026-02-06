# backend/tests/unit/test_caculinha_bi_agent.py

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent, FieldMapper, CodeGenAgent
from app.core.tools.une_tools import (
    calcular_abastecimento_une, calcular_mc_produto, calcular_preco_final_une,
    validar_transferencia_produto, sugerir_transferencias_automaticas, encontrar_rupturas_criticas
)
from app.core.utils.error_handler import APIError

class MockLLM:
    """A mock LLM that can simulate responses."""
    def __init__(self, responses: dict):
        self._responses = responses
        self._call_count = {}

    def invoke(self, prompt: str):
        # Find the response that matches the beginning of the prompt
        for key, value in self._responses.items():
            if key in prompt:
                if isinstance(value, list): # Handle multiple responses for same key
                    current_count = self._call_count.get(key, 0)
                    response_to_return = value[current_count % len(value)]
                    self._call_count[key] = current_count + 1
                    return response_to_return
                return value
        
        # Default to a generic code generation response if no specific match
        return {
            "code": "import polars as pl\nfinal_output = {'result': 'Default code response.'}",
            "chart_spec": {}
        }

@pytest.fixture
def mock_llm():
    # Define expected LLM responses based on prompt keywords
    responses = {
        "selecionar a ferramenta mais apropriada": {
            "tool": "calcular_abastecimento_une", 
            "params": {"une_id": 1, "segmento": "A"}
        },
        "gerador de filtros JSON": {
            "produto": "Camisa",
            "regiao": "Sudeste"
        }
    }
    return MockLLM(responses)

@pytest.fixture
def mock_field_mapper():
    mapper = MagicMock(spec=FieldMapper)
    mapper.map_term.side_effect = lambda x: {"produto": "produto_id", "une": "une_id"}.get(x.lower(), x)
    mapper.get_known_fields.return_value = ["produto", "une", "segmento"]
    return mapper

@pytest.fixture
def mock_code_gen_agent():
    agent = MagicMock(spec=CodeGenAgent)
    agent.generate_and_execute_python_code.return_value = {"type": "code_result", "result": "Mocked code execution result"}
    return agent

@pytest.fixture
def caculinha_bi_agent(mock_llm, mock_code_gen_agent, mock_field_mapper):
    # Ensure CaculinhaBIAgent uses the mock LLM for its internal prompt chains
    # This requires a bit of patching or careful construction if LLM is deeply integrated
    
    # Temporarily patch _load_prompt_template to return static content for testing
    with patch('backend.app.core.agents.caculinha_bi_agent._load_prompt_template') as mock_load_prompt:
        mock_load_prompt.side_effect = {
            "tool_routing_prompt.md": "system prompt for tool routing with {tool_names}",
            "json_filter_generation_prompt.md": "system prompt for json filter with {known_fields}"
        }.get

        agent = CaculinhaBIAgent(llm=mock_llm, code_gen_agent=mock_code_gen_agent, field_mapper=mock_field_mapper)
        return agent

# Test CaculinhaBIAgent
@pytest.mark.asyncio
async def test_caculinha_bi_agent_tool_routing(caculinha_bi_agent, mock_code_gen_agent):
    # Test a query that should trigger a tool
    query = "Calcule o abastecimento da UNE 1 no segmento A."
    
    # Mock the LLM call for tool routing
    caculinha_bi_agent.llm.invoke.return_value = {
        "tool": "calcular_abastecimento_une",
        "params": {"une_id": 1, "segmento": "A"}
    }
    
    # Mock the tool itself
    with patch('backend.app.core.tools.une_tools.calcular_abastecimento_une', return_value=[{"produto_id": 101, "necessidade": 50}]) as mock_tool:
        result = await caculinha_bi_agent.run(query)
        
        mock_tool.assert_called_once_with(une_id=1, segmento="A")
        assert result["type"] == "tool_result"
        assert result["tool_name"] == "calcular_abastecimento_une"
        assert result["result"] == [{"produto_id": 101, "necessidade": 50}]


@pytest.mark.asyncio
async def test_caculinha_bi_agent_code_generation(caculinha_bi_agent, mock_code_gen_agent):
    # Test a query that should trigger code generation
    query = "Me mostre um gráfico de vendas por região."
    
    # Mock the LLM call for tool routing to indicate code generation
    caculinha_bi_agent.llm.invoke.return_value = {
        "tool": "generate_and_execute_python_code", 
        "params": {"query": query}
    }
    
    result = await caculinha_bi_agent.run(query)
    
    mock_code_gen_agent.generate_and_execute_python_code.assert_called_once()
    assert result["type"] == "code_result"
    assert result["result"] == "Mocked code execution result"


@pytest.mark.asyncio
async def test_caculinha_bi_agent_json_filter_generation(caculinha_bi_agent):
    # This scenario is implicitly tested when a tool requires parameters extracted
    # or if there was a dedicated LLM call for filter generation.
    # For now, _extract_une_params directly extracts from query.
    query = "Validar transferencia do produto 101 da UNE 5 para UNE 10 quantidade 20."
    
    caculinha_bi_agent.llm.invoke.return_value = {
        "tool": "validar_transferencia_produto",
        "params": {
            "produto_id": 101,
            "une_origem": 5,
            "une_destino": 10,
            "quantidade": 20
        }
    }

    with patch('backend.app.core.tools.une_tools.validar_transferencia_produto', return_value={"status": "sucesso"}) as mock_tool:
        result = await caculinha_bi_agent.run(query)
        mock_tool.assert_called_once_with(produto_id=101, une_origem=5, une_destino=10, quantidade=20)
        assert result["type"] == "tool_result"
        assert result["result"]["status"] == "sucesso"


@pytest.mark.asyncio
async def test_caculinha_bi_agent_error_handling(caculinha_bi_agent, mock_code_gen_agent):
    # Simulate an error from a tool
    query = "Calcule o abastecimento da UNE 1 que vai falhar."
    caculinha_bi_agent.llm.invoke.return_value = {
        "tool": "calcular_abastecimento_une", 
        "params": {"une_id": 1}
    }
    
    with patch('backend.app.core.tools.une_tools.calcular_abastecimento_une', side_effect=ValueError("Simulated tool error")) as mock_tool:
        result = await caculinha_bi_agent.run(query)
        assert result["type"] == "error"
        assert "Simulated tool error" in result["message"]

@pytest.mark.asyncio
async def test_caculinha_bi_agent_unrecognized_query(caculinha_bi_agent, mock_code_gen_agent):
    # Query not matching any tool, should default to CodeGenAgent
    query = "Qual a correlação entre temperatura e vendas?"
    caculinha_bi_agent.llm.invoke.return_value = {
        "tool": "unknown_tool", 
        "params": {}
    } # Simulate LLM choosing an unknown tool or just returning text
    
    result = await caculinha_bi_agent.run(query)
    mock_code_gen_agent.generate_and_execute_python_code.assert_called_once()
    assert result["type"] == "code_result"
