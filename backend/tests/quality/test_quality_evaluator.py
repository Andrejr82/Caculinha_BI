import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from backend.application.agents.quality_evaluator_agent import QualityEvaluatorAgent
from backend.application.agents.base_agent import AgentRequest

@pytest.fixture
def mock_llm():
    mock = MagicMock()
    mock.generate_response = AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_evaluate_response_ok(mock_llm):
    # Setup mock response for OK scenario
    mock_llm.generate_response.return_value = json.dumps({
        "scores": {"quality": 0.9, "utility": 0.9, "groundedness": 1.0},
        "reasoning": {"quality": "Good", "utility": "High", "groundedness": "Perfect"},
        "final_decision": "OK"
    })
    
    agent = QualityEvaluatorAgent(llm_client=mock_llm)
    query = "Como estão as vendas?"
    response = "As vendas estão excelentes, crescendo 10%."
    rag_context = "Vendas cresceram 10% no período."
    
    result = await agent.evaluate_response(query, response, rag_context)
    
    assert result["final_decision"] == "OK"
    assert result["scores"]["groundedness"] == 1.0
    mock_llm.generate_response.assert_called_once()

@pytest.mark.asyncio
async def test_evaluate_response_block(mock_llm):
    # Setup mock response for BLOCK scenario (hallucination)
    mock_llm.generate_response.return_value = json.dumps({
        "scores": {"quality": 0.8, "utility": 0.5, "groundedness": 0.2},
        "reasoning": {"quality": "Ok", "utility": "Low", "groundedness": "Alucinação detectada"},
        "final_decision": "BLOCK"
    })
    
    agent = QualityEvaluatorAgent(llm_client=mock_llm)
    query = "Qual o estoque da Loja 1?"
    response = "O estoque da Loja 1 é de 500 unidades."
    # RAG diz outra coisa ou nada
    rag_context = "Estoque Loja 1: 10 unidades."
    
    result = await agent.evaluate_response(query, response, rag_context)
    
    assert result["final_decision"] == "BLOCK"
    assert result["scores"]["groundedness"] < 0.5

@pytest.mark.asyncio
async def test_json_parsing_resilience(mock_llm):
    # LLM sometimes returns markdown boxes
    mock_llm.generate_response.return_value = "```json\n{\"scores\": {\"quality\": 0.9, \"utility\": 0.9, \"groundedness\": 0.9}, \"final_decision\": \"OK\"}\n```"
    
    agent = QualityEvaluatorAgent(llm_client=mock_llm)
    result = await agent.evaluate_response("query", "resp", "rag")
    
    assert result["final_decision"] == "OK"

@pytest.mark.asyncio
async def test_fallback_on_error(mock_llm):
    # LLM fails
    mock_llm.generate_response.side_effect = Exception("API Down")
    
    agent = QualityEvaluatorAgent(llm_client=mock_llm)
    result = await agent.evaluate_response("query", "resp", "rag")
    
    assert result["final_decision"] == "WARNING"
    assert "error" in result["reasoning"]
