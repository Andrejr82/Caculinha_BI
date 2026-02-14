"""
Legacy feedback endpoint module kept for backward-compatible test patching.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.pipeline_factory import get_pipeline_factory

router = APIRouter(prefix="/feedback", tags=["Governance"])


class FeedbackRequest(BaseModel):
    request_id: str = Field(...)
    user_rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None)


@router.post("")
async def submit_feedback(data: FeedbackRequest):
    factory = get_pipeline_factory()
    memory_agent = factory.get_memory_agent()
    success = await memory_agent.save_feedback(
        request_id=data.request_id,
        rating=data.user_rating,
        comment=data.comment,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao salvar feedback")
    return {"status": "success", "message": "Feedback registrado com sucesso"}

