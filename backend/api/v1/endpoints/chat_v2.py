"""
Chat Endpoint — API de Chat

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

from backend.application.agents.base_agent import AgentRequest
from backend.application.agents.orchestrator_agent import OrchestratorAgent

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    """Request para chat."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response do chat."""
    response: str
    conversation_id: str
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None


# Singleton do orchestrator (injetado via dependency)
_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """Dependency injection do orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        # Lazy init sem dependências por enquanto
        _orchestrator = OrchestratorAgent()
    return _orchestrator


def set_orchestrator(orchestrator: OrchestratorAgent):
    """Configura orchestrator (chamado no startup)."""
    global _orchestrator
    _orchestrator = orchestrator


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    tenant_id: str = "default",
    user_id: str = "anonymous",
    orchestrator: OrchestratorAgent = Depends(get_orchestrator),
):
    """
    Endpoint principal de chat.
    
    Pipeline:
    1. Recebe mensagem do usuário
    2. Passa pelo OrchestratorAgent
    3. Retorna resposta gerada
    """
    logger.info("chat_request", message_len=len(request.message), tenant_id=tenant_id)
    
    # Cria ou usa conversation_id
    conversation_id = request.conversation_id or f"conv-{tenant_id}-{user_id}"
    
    # Monta request do agente
    agent_request = AgentRequest(
        content=request.message,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        user_id=user_id,
        metadata=request.metadata,
    )
    
    try:
        # Executa pipeline
        response = await orchestrator.run(agent_request)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error or "Erro no processamento")
        
        return ChatResponse(
            response=response.content,
            conversation_id=conversation_id,
            success=True,
            metadata=response.metadata,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
