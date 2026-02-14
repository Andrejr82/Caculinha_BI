"""
Chat Endpoint

Endpoint principal de chat conversacional com suporte a SSE streaming.

Uso:
    POST /api/v2/chat          → Chat síncrono
    POST /api/v2/chat/stream   → Chat com streaming SSE

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import structlog

# Carregar .env com path explícito
from dotenv import load_dotenv
_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)


logger = structlog.get_logger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class ChatMessage(BaseModel):
    """Mensagem de chat."""
    role: str = Field(..., description="Role: user, assistant, system")
    content: str = Field(..., description="Conteúdo da mensagem")


class ChatRequest(BaseModel):
    """Requisição de chat."""
    message: str = Field(..., description="Mensagem do usuário")
    conversation_id: Optional[str] = Field(None, description="ID da conversa")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contexto adicional")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Como estão as vendas da loja 1685?",
                "conversation_id": "conv-123",
            }
        }


class ChatResponse(BaseModel):
    """Resposta de chat."""
    content: str = Field(..., description="Resposta do agente")
    conversation_id: str = Field(..., description="ID da conversa")
    agent_name: str = Field(..., description="Nome do agente que respondeu")
    execution_time_ms: float = Field(..., description="Tempo de execução em ms")
    tool_calls: List[str] = Field(default_factory=list, description="Ferramentas utilizadas")
    insights: List[Dict[str, Any]] = Field(default_factory=list, description="Insights gerados")


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_tenant_id(request: Request) -> str:
    """Extrai tenant_id do header ou usa default."""
    return request.headers.get("X-Tenant-ID", "default-tenant")


def get_user_id(request: Request) -> str:
    """Extrai user_id do header ou usa default."""
    return request.headers.get("X-User-ID", "anonymous")


async def get_orchestrator():
    """Cria e retorna o OrchestratorAgent configurado."""
    from backend.application.agents import (
        OrchestratorAgent,
        SQLAgent,
        InsightAgent,
        ForecastAgent,
        MetadataAgent,
        TenantAgent,
        SecurityAgent,
        MonitoringAgent,
    )
    from backend.infrastructure.adapters.llm import GeminiAdapter
    from backend.infrastructure.adapters.data import DuckDBAdapter
    
    # Criar adapters
    llm = GeminiAdapter()
    data_source = DuckDBAdapter()
    
    # Criar agentes especializados
    sql_agent = SQLAgent(llm=llm, data_source=data_source)
    insight_agent = InsightAgent(llm=llm)
    forecast_agent = ForecastAgent(llm=llm, data_source=data_source)
    metadata_agent = MetadataAgent(llm=llm, data_source=data_source)
    tenant_agent = TenantAgent()
    security_agent = SecurityAgent()
    monitoring_agent = MonitoringAgent()
    
    # Criar orquestrador
    orchestrator = OrchestratorAgent(llm=llm)
    
    # Registrar agentes
    orchestrator.register_agent(sql_agent)
    orchestrator.register_agent(insight_agent)
    orchestrator.register_agent(forecast_agent)
    orchestrator.register_agent(metadata_agent)
    orchestrator.register_agent(tenant_agent)
    orchestrator.register_agent(security_agent)
    orchestrator.register_agent(monitoring_agent)
    
    return orchestrator


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id),
):
    """
    Endpoint de chat síncrono.
    
    Processa a mensagem do usuário através do OrchestratorAgent
    e retorna a resposta completa.
    
    Args:
        request: Requisição de chat com a mensagem
        tenant_id: ID do tenant (header X-Tenant-ID)
        user_id: ID do usuário (header X-User-ID)
    
    Returns:
        Resposta do agente com conteúdo, métricas e insights
    """
    from backend.domain.ports.agent_port import AgentRequest
    
    conversation_id = request.conversation_id or str(uuid4())
    
    logger.info(
        "chat_request_received",
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        message_preview=request.message[:100],
    )
    
    try:
        # Obter orquestrador
        orchestrator = await get_orchestrator()
        
        # Criar requisição do agente
        agent_request = AgentRequest(
            message=request.message,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            context=request.context or {},
        )
        
        # Executar
        response = await orchestrator.run(agent_request)
        
        logger.info(
            "chat_request_completed",
            conversation_id=conversation_id,
            success=response.success,
            execution_time_ms=response.execution_time_ms,
        )
        
        return ChatResponse(
            content=response.content,
            conversation_id=conversation_id,
            agent_name=response.agent_name,
            execution_time_ms=response.execution_time_ms,
            tool_calls=response.tool_calls,
            insights=response.insights,
        )
        
    except Exception as e:
        logger.error("chat_request_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id),
):
    """
    Endpoint de chat com streaming SSE.
    
    Processa a mensagem e retorna a resposta em chunks
    via Server-Sent Events.
    
    Args:
        request: Requisição de chat
        tenant_id: ID do tenant
        user_id: ID do usuário
    
    Returns:
        StreamingResponse com eventos SSE
    """
    import json
    from backend.domain.ports.agent_port import AgentRequest
    
    conversation_id = request.conversation_id or str(uuid4())
    
    async def generate_events():
        try:
            # Evento de início
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\n\n"
            
            # Obter orquestrador
            orchestrator = await get_orchestrator()
            
            # Criar requisição
            agent_request = AgentRequest(
                message=request.message,
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                user_id=user_id,
                context=request.context or {},
            )
            
            # Executar (por enquanto, não-streaming)
            response = await orchestrator.run(agent_request)
            
            # Enviar resposta em chunks
            content = response.content
            chunk_size = 50
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # Evento de fim
            yield f"data: {json.dumps({'type': 'end', 'agent_name': response.agent_name, 'execution_time_ms': response.execution_time_ms})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    Obtém o histórico de uma conversa.
    
    Args:
        conversation_id: ID da conversa
        tenant_id: ID do tenant
    
    Returns:
        Lista de mensagens da conversa
    """
    # TODO: Implementar persistência de conversas
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "message": "Histórico de conversas será implementado na FASE 6"
    }
