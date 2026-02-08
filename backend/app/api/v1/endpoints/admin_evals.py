"""
Admin Evaluations Endpoints - ADMIN ONLY
List, view, and manage response quality evaluations.

All endpoints require admin role or user@agentbi.com email.
"""

from datetime import datetime
from typing import Annotated, Dict, Any, List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.app.api.dependencies import require_admin
from backend.app.infrastructure.database.models import User
from backend.app.core.evaluations_repository import evaluations_repo

router = APIRouter(prefix="/admin/evals", tags=["Admin Evaluations"])
logger = logging.getLogger(__name__)


# ==================== Response Models ====================

class EvaluationSummary(BaseModel):
    """Summary of an evaluation for list view."""
    request_id: str
    user_id: Optional[str] = None
    overall_score: float
    prompt_summary: Optional[str] = None
    created_at: str
    has_feedback: bool = False

class EvaluationDetail(BaseModel):
    """Full evaluation details."""
    request_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    prompt: Optional[str] = None
    response: Optional[str] = None
    overall_score: float
    dimension_scores: Dict[str, float] = {}
    reasons: List[str] = []
    latency_ms: Optional[float] = None
    retrieved_doc_ids: List[str] = []
    feedback: List[Dict[str, Any]] = []
    created_at: str

class EvaluationsListResponse(BaseModel):
    """Paginated list of evaluations."""
    evaluations: List[EvaluationSummary]
    total: int
    limit: int
    offset: int

class FeedbackRequest(BaseModel):
    """Request to add feedback to an evaluation."""
    feedback_type: str  # "thumbs_up" or "thumbs_down"
    comment: Optional[str] = None


# ==================== Endpoints ====================

@router.get("", response_model=EvaluationsListResponse)
async def list_evaluations(
    current_user: Annotated[User, Depends(require_admin)],
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
):
    """
    List all evaluations with pagination and filters.
    
    ADMIN ONLY.
    """
    evals = evaluations_repo.get_all(
        limit=limit,
        offset=offset,
        min_score=min_score,
        max_score=max_score
    )
    
    summaries = []
    for e in evals:
        summaries.append(EvaluationSummary(
            request_id=e.get("request_id", ""),
            user_id=e.get("user_id"),
            overall_score=e.get("overall_score", 0),
            prompt_summary=e.get("prompt", "")[:100] if e.get("prompt") else None,
            created_at=e.get("created_at", ""),
            has_feedback=bool(e.get("feedback"))
        ))
    
    return EvaluationsListResponse(
        evaluations=summaries,
        total=evaluations_repo.count(),
        limit=limit,
        offset=offset
    )


@router.get("/{request_id}", response_model=EvaluationDetail)
async def get_evaluation(
    request_id: str,
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Get detailed evaluation by request_id.
    
    ADMIN ONLY.
    """
    evaluation = evaluations_repo.get(request_id)
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    
    return EvaluationDetail(
        request_id=evaluation.get("request_id", ""),
        user_id=evaluation.get("user_id"),
        tenant_id=evaluation.get("tenant_id"),
        prompt=evaluation.get("prompt"),
        response=evaluation.get("response"),
        overall_score=evaluation.get("overall_score", 0),
        dimension_scores=evaluation.get("dimension_scores", {}),
        reasons=evaluation.get("reasons", []),
        latency_ms=evaluation.get("latency_ms"),
        retrieved_doc_ids=evaluation.get("retrieved_doc_ids", []),
        feedback=evaluation.get("feedback", []),
        created_at=evaluation.get("created_at", "")
    )


@router.post("/{request_id}/feedback")
async def add_feedback(
    request_id: str,
    feedback: FeedbackRequest,
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Add feedback to an evaluation.
    
    Feedback is stored but does NOT automatically change the score.
    ADMIN ONLY.
    """
    if feedback.feedback_type not in ["thumbs_up", "thumbs_down"]:
        raise HTTPException(status_code=400, detail="Tipo de feedback inválido")
    
    success = evaluations_repo.add_feedback(
        request_id=request_id,
        feedback_type=feedback.feedback_type,
        comment=feedback.comment
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    
    return {"status": "ok", "message": "Feedback adicionado com sucesso"}
