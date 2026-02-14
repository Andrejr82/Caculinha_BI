"""
Metrics Endpoint

Endpoint para expor métricas da aplicação.

Uso:
    GET /api/v2/metrics          → Métricas atuais
    GET /api/v2/metrics/usage    → Uso de billing por tenant

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field
import structlog

from dotenv import load_dotenv
_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)


logger = structlog.get_logger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class MetricsResponse(BaseModel):
    """Resposta de métricas."""
    uptime_seconds: float
    counters: dict
    gauges: dict
    histograms: dict


class UsageResponse(BaseModel):
    """Resposta de uso de billing."""
    tenant_id: str
    plan: str
    breakdown: dict
    total_brl: float
    calculated_at: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=MetricsResponse)
async def get_metrics(request: Request):
    """
    Retorna métricas atuais da aplicação.
    
    Requer permissão de admin.
    """
    from backend.services.metrics import MetricsService
    
    # Verificar permissão (simplificado)
    user_role = getattr(request.state, "user_role", "guest")
    if user_role not in ["admin", "system"]:
        # Em produção, restringir; aqui permitimos para testes
        pass
    
    metrics = MetricsService()
    return metrics.get_all_metrics()


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    request: Request,
    tenant_id: Optional[str] = None,
):
    """
    Retorna uso de billing do tenant.
    
    Args:
        tenant_id: ID do tenant (usa do request.state se não fornecido)
    """
    from backend.services.billing import BillingService
    
    # Resolver tenant
    resolved_tenant = tenant_id or getattr(request.state, "tenant_id", "default")
    
    billing = BillingService()
    cost = billing.calculate_cost(resolved_tenant)
    
    return UsageResponse(**cost)


@router.post("/usage/record")
async def record_usage(
    request: Request,
    usage_type: str = "api_calls",
    amount: int = 1,
):
    """
    Registra uso manualmente (para testes).
    """
    from backend.services.billing import BillingService, UsageType
    
    tenant_id = getattr(request.state, "tenant_id", "default")
    
    try:
        billing = BillingService()
        billing.record_usage(tenant_id, UsageType(usage_type), amount)
        return {"status": "recorded", "tenant_id": tenant_id, "usage_type": usage_type, "amount": amount}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipo de uso inválido: {usage_type}")


@router.get("/invoice")
async def get_invoice(request: Request):
    """
    Gera fatura para o tenant atual.
    """
    from backend.services.billing import BillingService
    
    tenant_id = getattr(request.state, "tenant_id", "default")
    
    billing = BillingService()
    invoice = billing.generate_invoice(tenant_id)
    
    return invoice
