"""
Port: MetricsPort

Interface abstrata para coleta de métricas e observabilidade.
Implementada por: OpenTelemetryAdapter, PrometheusAdapter

Uso:
    from backend.domain.ports import MetricsPort
    
    class OpenTelemetryAdapter(MetricsPort):
        def increment_counter(self, name, value=1, tags=None):
            ...

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from contextlib import contextmanager


class MetricsPort(ABC):
    """
    Interface abstrata para coleta de métricas.
    
    Esta é a porta para observabilidade e monitoramento.
    Implementações concretas em infrastructure/observability/
    
    Example:
        >>> class OpenTelemetryAdapter(MetricsPort):
        ...     def increment_counter(self, name, value=1, tags=None):
        ...         self.meter.increment(name, value, tags)
    """
    
    @abstractmethod
    def increment_counter(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Incrementa um contador.
        
        Args:
            name: Nome da métrica
            value: Valor a incrementar
            tags: Tags/labels adicionais
        """
        pass
    
    @abstractmethod
    def record_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Registra um valor de gauge.
        
        Args:
            name: Nome da métrica
            value: Valor atual
            tags: Tags/labels adicionais
        """
        pass
    
    @abstractmethod
    def record_histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Registra um valor em um histograma.
        
        Args:
            name: Nome da métrica
            value: Valor a registrar
            tags: Tags/labels adicionais
        """
        pass
    
    @abstractmethod
    @contextmanager
    def timer(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Context manager para medir duração de operações.
        
        Args:
            name: Nome da métrica de tempo
            tags: Tags/labels adicionais
        
        Example:
            >>> with metrics.timer("agent_execution_time"):
            ...     result = await agent.run()
        """
        pass
    
    @abstractmethod
    def record_event(
        self,
        name: str,
        data: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Registra um evento customizado.
        
        Args:
            name: Nome do evento
            data: Dados do evento
            tags: Tags/labels adicionais
        """
        pass
    
    @abstractmethod
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Retorna snapshot das métricas atuais.
        
        Returns:
            Dicionário com métricas
        """
        pass
