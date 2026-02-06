"""
Query Monitor - Monitoramento de Performance de Queries

Rastreia tempo de execução, identifica queries lentas e gera métricas.
Baseado nas recomendações do Database Architect.
"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class QueryStats:
    """Estatísticas de uma query."""
    query: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    slow_count: int = 0  # Quantas vezes foi considerada lenta
    
    def update(self, execution_time: float, is_slow: bool = False):
        """Atualiza estatísticas com nova execução."""
        self.count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.count
        
        if is_slow:
            self.slow_count += 1


class QueryMonitor:
    """
    Monitor de performance de queries.
    
    Features:
    - Rastreamento de tempo de execução
    - Detecção de queries lentas
    - Estatísticas agregadas
    - Top N queries mais lentas
    """
    
    def __init__(self, slow_query_threshold: float = 1.0):
        """
        Inicializa o monitor.
        
        Args:
            slow_query_threshold: Threshold em segundos para query lenta (default: 1s)
        """
        self.slow_query_threshold = slow_query_threshold
        self._stats: Dict[str, QueryStats] = defaultdict(lambda: QueryStats(query=""))
        self._lock = Lock()
        
        # Métricas globais
        self.total_queries = 0
        self.total_slow_queries = 0
        
        logger.info(f"QueryMonitor inicializado: threshold={slow_query_threshold}s")
    
    def _normalize_query(self, query: str) -> str:
        """
        Normaliza query para agrupamento.
        
        Remove valores literais para agrupar queries similares.
        
        Args:
            query: Query SQL original
            
        Returns:
            Query normalizada
        """
        # Simplificação: remover espaços extras e converter para minúsculas
        normalized = " ".join(query.strip().lower().split())
        
        # TODO: Implementar normalização mais sofisticada
        # - Substituir valores literais por placeholders
        # - Remover comentários
        # - Padronizar formatação
        
        return normalized
    
    def track_query(
        self, 
        query: str, 
        execution_time: float,
        params: Optional[Dict] = None
    ):
        """
        Rastreia execução de uma query.
        
        Args:
            query: Query SQL executada
            execution_time: Tempo de execução em segundos
            params: Parâmetros da query (opcional)
        """
        self.total_queries += 1
        is_slow = execution_time > self.slow_query_threshold
        
        if is_slow:
            self.total_slow_queries += 1
            logger.warning(
                f"[WARNING] SLOW QUERY ({execution_time:.3f}s): {query[:100]}..."
            )
        
        # Normalizar query para agrupamento
        normalized_query = self._normalize_query(query)
        
        with self._lock:
            if normalized_query not in self._stats:
                self._stats[normalized_query] = QueryStats(query=query)
            
            self._stats[normalized_query].update(execution_time, is_slow)
    
    def get_slow_queries(self, limit: int = 10) -> List[QueryStats]:
        """
        Retorna as N queries mais lentas.
        
        Args:
            limit: Número máximo de queries para retornar
            
        Returns:
            Lista de QueryStats ordenada por avg_time (decrescente)
        """
        with self._lock:
            sorted_stats = sorted(
                self._stats.values(),
                key=lambda s: s.avg_time,
                reverse=True
            )
            return sorted_stats[:limit]
    
    def get_most_frequent(self, limit: int = 10) -> List[QueryStats]:
        """
        Retorna as N queries mais executadas.
        
        Args:
            limit: Número máximo de queries para retornar
            
        Returns:
            Lista de QueryStats ordenada por count (decrescente)
        """
        with self._lock:
            sorted_stats = sorted(
                self._stats.values(),
                key=lambda s: s.count,
                reverse=True
            )
            return sorted_stats[:limit]
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas globais.
        
        Returns:
            Dicionário com métricas
        """
        slow_query_rate = (
            self.total_slow_queries / self.total_queries * 100
            if self.total_queries > 0 else 0
        )
        
        with self._lock:
            total_time = sum(s.total_time for s in self._stats.values())
            avg_time = (
                total_time / self.total_queries
                if self.total_queries > 0 else 0
            )
        
        return {
            "total_queries": self.total_queries,
            "total_slow_queries": self.total_slow_queries,
            "slow_query_rate": round(slow_query_rate, 2),
            "unique_queries": len(self._stats),
            "avg_execution_time": round(avg_time, 3),
            "threshold": self.slow_query_threshold
        }
    
    def reset_stats(self):
        """Reseta todas as estatísticas."""
        with self._lock:
            self._stats.clear()
            self.total_queries = 0
            self.total_slow_queries = 0
        
        logger.info("Estatísticas resetadas")


# Singleton instance
_monitor_instance: Optional[QueryMonitor] = None


def get_query_monitor(slow_query_threshold: float = 1.0) -> QueryMonitor:
    """
    Retorna instância singleton do query monitor.
    
    Args:
        slow_query_threshold: Threshold para query lenta em segundos
        
    Returns:
        QueryMonitor instance
    """
    global _monitor_instance
    
    if _monitor_instance is None:
        _monitor_instance = QueryMonitor(slow_query_threshold=slow_query_threshold)
    
    return _monitor_instance


if __name__ == "__main__":
    # Teste do monitor
    monitor = QueryMonitor(slow_query_threshold=0.5)
    
    # Simular queries
    monitor.track_query("SELECT * FROM admmat WHERE PRODUTO = '1'", 0.1)
    monitor.track_query("SELECT * FROM admmat WHERE PRODUTO = '2'", 0.8)  # Slow
    monitor.track_query("SELECT * FROM admmat WHERE PRODUTO = '1'", 0.15)
    
    # Stats
    stats = monitor.get_stats()
    print(f"Estatísticas Globais: {stats}")
    
    # Slow queries
    slow = monitor.get_slow_queries(limit=5)
    print(f"\nQueries Lentas:")
    for s in slow:
        print(f"  - {s.query[:50]}... (avg: {s.avg_time:.3f}s, count: {s.count})")
