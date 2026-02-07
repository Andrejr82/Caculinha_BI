"""
BillingService - Serviço de Billing (Placeholder)

Placeholder para integração futura com sistema de cobrança.

Uso:
    from backend.services import BillingService
    
    billing = BillingService()
    usage = billing.get_usage("tenant-123")
    billing.record_usage("tenant-123", tokens=1000)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

import structlog


logger = structlog.get_logger(__name__)


class BillingPlan(str, Enum):
    """Planos de cobrança disponíveis."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UsageType(str, Enum):
    """Tipos de uso para cobrança."""
    API_CALLS = "api_calls"
    TOKENS = "tokens"
    STORAGE_MB = "storage_mb"
    AGENTS = "agents"


# Preços por unidade (em centavos)
PRICING = {
    BillingPlan.FREE: {
        UsageType.API_CALLS: 0,
        UsageType.TOKENS: 0,
        UsageType.STORAGE_MB: 0,
        UsageType.AGENTS: 0,
    },
    BillingPlan.PRO: {
        UsageType.API_CALLS: 0.1,  # R$ 0,001 por chamada
        UsageType.TOKENS: 0.01,   # R$ 0,0001 por token
        UsageType.STORAGE_MB: 5,  # R$ 0,05 por MB
        UsageType.AGENTS: 100,    # R$ 1,00 por agente custom
    },
    BillingPlan.ENTERPRISE: {
        UsageType.API_CALLS: 0.05,
        UsageType.TOKENS: 0.005,
        UsageType.STORAGE_MB: 2,
        UsageType.AGENTS: 50,
    },
}


class BillingService:
    """
    Serviço de cobrança (Placeholder).
    
    Rastreia uso e calcula custos. Em produção, integrar com
    Stripe, PagSeguro, ou sistema interno de billing.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Uso por tenant: {tenant_id: {usage_type: count}}
        self._usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Plano por tenant
        self._plans: Dict[str, BillingPlan] = {}
        
        # Histórico de transações
        self._transactions: List[Dict] = []
        
        self._initialized = True
        logger.info("billing_service_initialized")
    
    # =========================================================================
    # USAGE TRACKING
    # =========================================================================
    
    def record_usage(
        self,
        tenant_id: str,
        usage_type: UsageType = UsageType.API_CALLS,
        amount: int = 1,
    ):
        """
        Registra uso para um tenant.
        
        Args:
            tenant_id: ID do tenant
            usage_type: Tipo de uso
            amount: Quantidade
        """
        self._usage[tenant_id][usage_type.value] += amount
        
        logger.debug(
            "usage_recorded",
            tenant_id=tenant_id,
            usage_type=usage_type.value,
            amount=amount,
        )
    
    def get_usage(self, tenant_id: str) -> Dict[str, int]:
        """
        Retorna o uso atual de um tenant.
        
        Args:
            tenant_id: ID do tenant
        
        Returns:
            Dicionário com uso por tipo
        """
        return dict(self._usage.get(tenant_id, {}))
    
    def reset_usage(self, tenant_id: str):
        """Reseta o uso de um tenant (para novo ciclo de billing)."""
        if tenant_id in self._usage:
            del self._usage[tenant_id]
            logger.info("usage_reset", tenant_id=tenant_id)
    
    # =========================================================================
    # PLANS
    # =========================================================================
    
    def set_plan(self, tenant_id: str, plan: BillingPlan):
        """Define o plano de um tenant."""
        self._plans[tenant_id] = plan
        logger.info("plan_set", tenant_id=tenant_id, plan=plan.value)
    
    def get_plan(self, tenant_id: str) -> BillingPlan:
        """Retorna o plano de um tenant."""
        return self._plans.get(tenant_id, BillingPlan.FREE)
    
    # =========================================================================
    # COST CALCULATION
    # =========================================================================
    
    def calculate_cost(self, tenant_id: str) -> Dict[str, Any]:
        """
        Calcula o custo atual de um tenant.
        
        Args:
            tenant_id: ID do tenant
        
        Returns:
            Dicionário com breakdown de custos
        """
        plan = self.get_plan(tenant_id)
        usage = self.get_usage(tenant_id)
        pricing = PRICING[plan]
        
        breakdown = {}
        total = 0
        
        for usage_type, amount in usage.items():
            try:
                price = pricing[UsageType(usage_type)]
                cost = amount * price / 100  # Converter centavos para reais
                breakdown[usage_type] = {
                    "amount": amount,
                    "unit_price": price,
                    "cost": cost,
                }
                total += cost
            except (KeyError, ValueError):
                pass
        
        return {
            "tenant_id": tenant_id,
            "plan": plan.value,
            "breakdown": breakdown,
            "total_brl": round(total, 2),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    
    # =========================================================================
    # INVOICES (Placeholder)
    # =========================================================================
    
    def generate_invoice(self, tenant_id: str) -> Dict[str, Any]:
        """
        Gera uma fatura para o tenant.
        
        Args:
            tenant_id: ID do tenant
        
        Returns:
            Dados da fatura
        """
        cost = self.calculate_cost(tenant_id)
        
        invoice = {
            "invoice_id": f"INV-{tenant_id[:8]}-{datetime.utcnow().strftime('%Y%m%d')}",
            "tenant_id": tenant_id,
            "plan": cost["plan"],
            "items": cost["breakdown"],
            "subtotal": cost["total_brl"],
            "tax": 0,  # Placeholder
            "total": cost["total_brl"],
            "currency": "BRL",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        
        self._transactions.append(invoice)
        logger.info("invoice_generated", invoice_id=invoice["invoice_id"])
        
        return invoice
    
    def get_invoices(self, tenant_id: str) -> List[Dict]:
        """Retorna faturas de um tenant."""
        return [t for t in self._transactions if t.get("tenant_id") == tenant_id]


# Funções de conveniência
def record_api_call(tenant_id: str):
    """Registra uma chamada de API."""
    BillingService().record_usage(tenant_id, UsageType.API_CALLS, 1)


def record_tokens(tenant_id: str, tokens: int):
    """Registra uso de tokens."""
    BillingService().record_usage(tenant_id, UsageType.TOKENS, tokens)
