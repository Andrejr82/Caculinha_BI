"""
Feedback Endpoint — Coleta de Satisfação do Usuário

Permite correlacionar a percepção humana com a auditoria automática.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.core.pipeline_factory import get_pipeline_factory

router = APIRouter(prefix="/feedback", tags=["Governance"])

class FeedbackRequest(BaseModel):
    request_id: str = Field(..., description="ID da requisição correlacionado (X-Request-Id)")
    user_rating: int = Field(..., ge=1, le=5, description="Nota de 1 a 5")
    comment: Optional[str] = Field(None, description="Comentário opcional do usuário")

@router.post("")
async def submit_feedback(data: FeedbackRequest):
    """
    Submete feedback para uma resposta específica.
    """
    factory = get_pipeline_factory()
    memory_agent = factory.get_memory_agent()
    
    success = await memory_agent.save_feedback(
        request_id=data.request_id,
        rating=data.user_rating,
        comment=data.comment
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao salvar feedback")
    
    return {"status": "success", "message": "Feedback registrado com sucesso"}
