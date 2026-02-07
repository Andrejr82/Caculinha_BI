"""
Feedback Endpoint — API de Feedback para Active Learning

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from typing import Optional, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    """Request de feedback."""
    conversation_id: str
    message_id: str
    rating: Literal["positive", "negative", "neutral"]
    feedback_text: Optional[str] = None
    correction: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response de feedback."""
    feedback_id: str
    success: bool = True


# Placeholder para feature store
_feature_store_agent = None


def set_feature_store_agent(agent):
    global _feature_store_agent
    _feature_store_agent = agent


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    tenant_id: str = "default",
):
    """
    Submete feedback do usuário para active learning.
    
    Pipeline:
    1. Armazena feedback como feature
    2. Marca para retraining
    """
    logger.info("feedback_received", conversation_id=request.conversation_id, rating=request.rating)
    
    try:
        feedback_id = f"fb-{request.conversation_id[:8]}"
        
        # Armazena como feature
        if _feature_store_agent:
            await _feature_store_agent.store_feature(
                tenant_id=tenant_id,
                entity_id=request.message_id,
                feature_name="user_feedback",
                value={
                    "rating": request.rating,
                    "text": request.feedback_text,
                    "correction": request.correction,
                },
                ttl=0,  # Permanente
            )
        
        return FeedbackResponse(feedback_id=feedback_id, success=True)
    
    except Exception as e:
        logger.error("feedback_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_feedback_stats(tenant_id: str = "default"):
    """Retorna estatísticas de feedback."""
    if not _feature_store_agent:
        return {"total": 0, "positive": 0, "negative": 0}
    
    stats = await _feature_store_agent.store.get_feature_stats(tenant_id, "user_feedback")
    return stats
