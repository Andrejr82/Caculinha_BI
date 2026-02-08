import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.application.agents.orchestrator_agent import OrchestratorAgent, PipelineContext
from backend.application.agents.base_agent import AgentRequest, AgentResponse
from backend.domain.entities.message import Message

@pytest.fixture
def mock_agents():
    return {
        "memory": MagicMock(),
        "insight": MagicMock(),
        "quality": MagicMock(),
    }

@pytest.mark.asyncio
async def test_orchestrator_block_flow(mock_agents):
    # Setup
    mock_agents["memory"].load_memory = AsyncMock(return_value=[])
    mock_agents["memory"].save_message = AsyncMock()
    
    mock_agents["insight"].generate_insight = AsyncMock(return_value="Resposta que será bloqueada")
    
    # Simula BLOCK por alucinação no auditor
    mock_agents["quality"].run = AsyncMock(return_value=AgentResponse(
        content=json.dumps({
            "scores": {"quality": 0.8, "utility": 0.5, "groundedness": 0.1},
            "final_decision": "BLOCK"
        }),
        agent_name="QualityEvaluatorAgent",
        success=True
    ))
    
    orchestrator = OrchestratorAgent(
        memory_agent=mock_agents["memory"],
        insight_agent=mock_agents["insight"],
        quality_evaluator_agent=mock_agents["quality"]
    )
    
    request = AgentRequest(
        content="Qual o estoque?",
        conversation_id="conv1",
        tenant_id="tenant1",
        user_id="user1"
    )
    
    response = await orchestrator._execute(request)
    
    # Verificações
    assert response.success
    assert "inconsistência nos dados" in response.content
    assert response.metadata["quality_decision"] == "BLOCK"
    
    # Memory Shield: save_message do assistente NÃO deve ter sido chamado para a resposta bloqueada
    # Mas o save_message do usuário SEMPRE é chamado (a lógica atual salva os dois se OK)
    # Na implementação atual do Orchestrator, se for BLOCK, o _step_save_memory retorna imediato
    mock_agents["memory"].save_message.assert_not_called()

@pytest.mark.asyncio
async def test_orchestrator_ok_flow(mock_agents):
    # Setup
    mock_agents["memory"].load_memory = AsyncMock(return_value=[])
    mock_agents["memory"].save_message = AsyncMock()
    mock_agents["insight"].generate_insight = AsyncMock(return_value="Resposta perfeita")
    
    mock_agents["quality"].run = AsyncMock(return_value=AgentResponse(
        content=json.dumps({
            "scores": {"quality": 0.9, "utility": 0.9, "groundedness": 0.9},
            "final_decision": "OK"
        }),
        agent_name="QualityEvaluatorAgent",
        success=True
    ))
    
    orchestrator = OrchestratorAgent(
        memory_agent=mock_agents["memory"],
        insight_agent=mock_agents["insight"],
        quality_evaluator_agent=mock_agents["quality"]
    )
    
    request = AgentRequest(content="Oi", conversation_id="c1", tenant_id="t1", user_id="u1")
    response = await orchestrator._execute(request)
    
    assert response.content == "Resposta perfeita"
    assert response.metadata["quality_decision"] == "OK"
    # Deve salvar User + Assistant messages
    assert mock_agents["memory"].save_message.call_count == 2
