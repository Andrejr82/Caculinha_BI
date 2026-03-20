from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.dependencies import get_current_active_user
from backend.app.infrastructure.database.models import User
from backend.app.schemas.basket_analysis import BasketAnalysisRequest, BasketAnalysisResponse
from backend.app.services.basket_analysis_service import BasketAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])
_basket_analysis_service = BasketAnalysisService()


def get_basket_analysis_service() -> BasketAnalysisService:
    return _basket_analysis_service


@router.post("/basket-analysis", response_model=BasketAnalysisResponse)
async def analyze_basket(
    request: BasketAnalysisRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[BasketAnalysisService, Depends(get_basket_analysis_service)],
) -> BasketAnalysisResponse:
    try:
        result = service.analyze(request, user=current_user)
        return BasketAnalysisResponse.model_validate(result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("basket analysis endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao executar basket analysis.",
        ) from exc
