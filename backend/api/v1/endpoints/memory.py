"""
Memory Endpoint — API de Memória

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/memory", tags=["Memory"])


class MessageResponse(BaseModel):
    """Mensagem na resposta."""
    id: str
    role: str
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    """Conversa com mensagens."""
    id: str
    tenant_id: str
    user_id: str
    title: Optional[str]
    messages: List[MessageResponse]
    message_count: int


class ConversationListItem(BaseModel):
    """Item na lista de conversas."""
    id: str
    title: Optional[str]
    updated_at: str
    message_count: int


# Placeholder para memory agent
_memory_agent = None


def set_memory_agent(agent):
    """Configura memory agent (chamado no startup)."""
    global _memory_agent
    _memory_agent = agent


def get_memory_agent():
    """Retorna memory agent."""
    if _memory_agent is None:
        raise HTTPException(status_code=503, detail="Memory agent not initialized")
    return _memory_agent


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """
    Recupera conversa com todas as mensagens.
    """
    agent = get_memory_agent()
    
    conv = await agent.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await agent.memory.get_all_messages(conversation_id)
    
    return ConversationResponse(
        id=conv.id,
        tenant_id=conv.tenant_id,
        user_id=conv.user_id,
        title=conv.title,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                timestamp=m.timestamp.isoformat(),
            )
            for m in messages
        ],
        message_count=len(messages),
    )


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Deleta conversa e todas as mensagens.
    """
    agent = get_memory_agent()
    
    deleted = await agent.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    logger.info("conversation_deleted", conversation_id=conversation_id)
    return {"success": True, "message": "Conversation deleted"}


@router.get("", response_model=List[ConversationListItem])
async def list_conversations(
    tenant_id: str = Query(...),
    user_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Lista conversas de um tenant/usuário.
    """
    agent = get_memory_agent()
    
    convs = await agent.memory.list_conversations(
        tenant_id=tenant_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    
    result = []
    for conv in convs:
        count = await agent.memory.count_messages(conv.id)
        result.append(ConversationListItem(
            id=conv.id,
            title=conv.title,
            updated_at=conv.updated_at.isoformat(),
            message_count=count,
        ))
    
    return result
