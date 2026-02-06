"""
Observability - Métricas de LLM
Rastreia latência, token usage e custos estimados

Baseado em melhores práticas 2024-2025 de observability
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LLMCallMetric:
    """Métrica de uma chamada LLM"""
    provider: str
    model: str
    tokens: int
    latency_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


class LLMMetrics:
    """Coleta e agrega métricas de LLM calls"""
    
    def __init__(self):
        self.calls = defaultdict(int)
        self.total_tokens = defaultdict(int)
        self.total_latency = defaultdict(float)
        self.errors = defaultdict(int)
        self.recent_calls: list[LLMCallMetric] = []
        self.max_recent = 100  # Manter últimas 100 chamadas
    
    def record_call(
        self,
        provider: str,
        model: str,
        tokens: int,
        latency: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Registra uma chamada LLM"""
        key = f"{provider}:{model}"
        self.calls[key] += 1
        self.total_tokens[key] += tokens
        self.total_latency[key] += latency
        
        if not success:
            self.errors[key] += 1
        
        # Adicionar às chamadas recentes
        metric = LLMCallMetric(
            provider=provider,
            model=model,
            tokens=tokens,
            latency_ms=latency * 1000,
            success=success,
            error=error
        )
        self.recent_calls.append(metric)
        
        # Manter apenas as últimas N chamadas
        if len(self.recent_calls) > self.max_recent:
            self.recent_calls.pop(0)
        
        # Log estruturado
        logger.info(
            "LLM call completed",
            extra={
                "provider": provider,
                "model": model,
                "tokens": tokens,
                "latency_ms": latency * 1000,
                "success": success,
                "error": error
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas agregadas"""
        metrics = {}
        for key in self.calls:
            avg_latency = (self.total_latency[key] / self.calls[key]) * 1000 if self.calls[key] > 0 else 0
            error_rate = self.errors[key] / self.calls[key] if self.calls[key] > 0 else 0
            
            metrics[key] = {
                "calls": self.calls[key],
                "total_tokens": self.total_tokens[key],
                "avg_latency_ms": round(avg_latency, 2),
                "errors": self.errors[key],
                "error_rate": round(error_rate, 4)
            }
        return metrics
    
    def get_recent_calls(self, limit: int = 10) -> list[dict]:
        """Retorna chamadas recentes"""
        recent = self.recent_calls[-limit:]
        return [
            {
                "provider": call.provider,
                "model": call.model,
                "tokens": call.tokens,
                "latency_ms": round(call.latency_ms, 2),
                "success": call.success,
                "timestamp": call.timestamp.isoformat(),
                "error": call.error
            }
            for call in recent
        ]


class LLMCallTracker:
    """Context manager para rastrear chamadas LLM"""
    
    def __init__(self, provider: str, model: str, metrics: LLMMetrics):
        self.provider = provider
        self.model = model
        self.metrics = metrics
        self.start_time = None
        self.tokens = 0
        self.success = True
        self.error = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency = time.time() - self.start_time
        self.success = exc_type is None
        
        if exc_val:
            self.error = str(exc_val)
        
        self.metrics.record_call(
            provider=self.provider,
            model=self.model,
            tokens=self.tokens,
            latency=latency,
            success=self.success,
            error=self.error
        )
        
        return False  # Não suprime exceções


# Instância global
llm_metrics = LLMMetrics()
