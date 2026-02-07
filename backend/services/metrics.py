"""
MetricsService - Serviço de Métricas e Observabilidade

Coleta e expõe métricas da aplicação para monitoramento.

Uso:
    from backend.services import MetricsService
    
    metrics = MetricsService()
    metrics.increment("chat_requests_total")
    metrics.observe("chat_latency_seconds", 0.5)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import time
from typing import Dict, Any, Optional, List
from collections import defaultdict
from datetime import datetime, timedelta
import threading

import structlog


logger = structlog.get_logger(__name__)


class MetricsService:
    """
    Serviço de coleta de métricas.
    
    Implementa contadores, gauges e histogramas para observabilidade.
    Em produção, pode ser integrado com Prometheus, DataDog, etc.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._labels: Dict[str, Dict[str, Any]] = {}
        self._start_time = time.time()
        self._initialized = True
        
        logger.info("metrics_service_initialized")
    
    # =========================================================================
    # COUNTERS
    # =========================================================================
    
    def increment(self, name: str, value: int = 1, labels: Optional[Dict] = None):
        """
        Incrementa um contador.
        
        Args:
            name: Nome da métrica
            value: Valor a incrementar
            labels: Labels opcionais
        """
        key = self._make_key(name, labels)
        self._counters[key] += value
    
    def get_counter(self, name: str, labels: Optional[Dict] = None) -> int:
        """Retorna valor atual de um contador."""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)
    
    # =========================================================================
    # GAUGES
    # =========================================================================
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict] = None):
        """
        Define valor de um gauge.
        
        Args:
            name: Nome da métrica
            value: Valor atual
            labels: Labels opcionais
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value
    
    def get_gauge(self, name: str, labels: Optional[Dict] = None) -> Optional[float]:
        """Retorna valor atual de um gauge."""
        key = self._make_key(name, labels)
        return self._gauges.get(key)
    
    # =========================================================================
    # HISTOGRAMS
    # =========================================================================
    
    def observe(self, name: str, value: float, labels: Optional[Dict] = None):
        """
        Registra uma observação em um histograma.
        
        Args:
            name: Nome da métrica
            value: Valor observado
            labels: Labels opcionais
        """
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        
        # Limitar histórico a últimas 1000 observações
        if len(self._histograms[key]) > 1000:
            self._histograms[key] = self._histograms[key][-1000:]
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict] = None) -> Dict:
        """Retorna estatísticas de um histograma."""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        
        if not values:
            return {"count": 0}
        
        sorted_values = sorted(values)
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "p50": sorted_values[len(values) // 2],
            "p95": sorted_values[int(len(values) * 0.95)] if len(values) >= 20 else None,
            "p99": sorted_values[int(len(values) * 0.99)] if len(values) >= 100 else None,
        }
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _make_key(self, name: str, labels: Optional[Dict] = None) -> str:
        """Cria chave única para métrica com labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def timer(self, name: str, labels: Optional[Dict] = None):
        """
        Context manager para medir tempo de execução.
        
        Usage:
            with metrics.timer("operation_duration"):
                do_something()
        """
        return _TimerContext(self, name, labels)
    
    # =========================================================================
    # EXPORT
    # =========================================================================
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Retorna todas as métricas em formato exportável."""
        return {
            "uptime_seconds": time.time() - self._start_time,
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in set(k.split("{")[0] for k in self._histograms.keys())
            },
        }
    
    def reset(self):
        """Reseta todas as métricas."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


class _TimerContext:
    """Context manager para medir tempo."""
    
    def __init__(self, metrics: MetricsService, name: str, labels: Optional[Dict]):
        self.metrics = metrics
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        duration = time.time() - self.start_time
        self.metrics.observe(self.name, duration, self.labels)


# Métricas pré-definidas para a aplicação
METRIC_NAMES = {
    # Counters
    "chat_requests_total": "Total de requisições de chat",
    "chat_errors_total": "Total de erros em chat",
    "auth_logins_total": "Total de logins",
    "auth_failures_total": "Total de falhas de autenticação",
    
    # Histograms
    "chat_latency_seconds": "Latência de requisições de chat",
    "agent_execution_seconds": "Tempo de execução dos agentes",
    "llm_latency_seconds": "Latência de chamadas ao LLM",
    "db_query_seconds": "Tempo de queries no banco",
    
    # Gauges
    "active_conversations": "Conversas ativas",
    "active_agents": "Agentes ativos",
}
