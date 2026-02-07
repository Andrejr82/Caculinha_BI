"""
Services - Inicialização

Este módulo contém serviços de infraestrutura da aplicação.

Uso:
    from backend.services import MetricsService, BillingService

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from backend.services.metrics import MetricsService
from backend.services.billing import BillingService
from backend.services.logging_config import setup_logging

__all__ = ["MetricsService", "BillingService", "setup_logging"]
