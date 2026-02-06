"""
Circuit Breaker Pattern - Resiliência para APIs Externas

Implementa circuit breaker para prevenir:
- Cascading failures
- Timeout excessivo
- Sobrecarga de serviços externos

Baseado nas recomendações do Backend Specialist.
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Estados do circuit breaker."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker para proteger chamadas a serviços externos.
    
    Features:
    - Detecção automática de falhas
    - Timeout configurável
    - Recovery automático
    - Métricas de estado
    
    States:
    - CLOSED: Funcionando normalmente
    - OPEN: Muitas falhas, rejeitando requests
    - HALF_OPEN: Testando se serviço recuperou
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Inicializa circuit breaker.
        
        Args:
            failure_threshold: Número de falhas antes de abrir
            recovery_timeout: Tempo em segundos antes de tentar recovery
            expected_exception: Tipo de exceção que conta como falha
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
        # Métricas
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_rejected = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executa função protegida pelo circuit breaker.
        
        Args:
            func: Função a ser executada
            *args, **kwargs: Argumentos da função
            
        Returns:
            Resultado da função
            
        Raises:
            CircuitBreakerOpenError: Se circuit está aberto
            Exception: Exceção original da função
        """
        self.total_calls += 1
        
        # Verificar estado
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker transitioning to HALF_OPEN")
            else:
                self.total_rejected += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. "
                    f"Will retry after {self.recovery_timeout}s"
                )
        
        try:
            # Executar função
            result = func(*args, **kwargs)
            
            # Sucesso
            self._on_success()
            return result
            
        except self.expected_exception as e:
            # Falha
            self._on_failure()
            raise
    
    def _on_success(self):
        """Callback quando chamada é bem-sucedida."""
        self.total_successes += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info(f"Circuit breaker recovered: HALF_OPEN -> CLOSED")
    
    def _on_failure(self):
        """Callback quando chamada falha."""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures. "
                f"Will retry after {self.recovery_timeout}s"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar recovery."""
        if self.last_failure_time is None:
            return False
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do circuit breaker."""
        success_rate = (
            self.total_successes / self.total_calls * 100
            if self.total_calls > 0 else 0
        )
        
        return {
            "state": self.state.value,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "total_rejected": self.total_rejected,
            "success_rate": round(success_rate, 2),
            "current_failures": self.failure_count,
            "threshold": self.failure_threshold
        }
    
    def reset(self):
        """Reseta circuit breaker manualmente."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")


class CircuitBreakerOpenError(Exception):
    """Exceção quando circuit breaker está aberto."""
    pass


# Decorator para aplicar circuit breaker
def circuit(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Decorator para proteger função com circuit breaker.
    
    Usage:
        @circuit(failure_threshold=3, recovery_timeout=30)
        async def call_external_api():
            ...
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception
    )
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Anexar breaker à função para acesso às stats
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


# Circuit breakers globais para serviços conhecidos
_circuit_breakers = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """
    Retorna circuit breaker para um serviço específico.
    
    Args:
        service_name: Nome do serviço (ex: "gemini_api", "supabase")
        
    Returns:
        CircuitBreaker instance
    """
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker()
    
    return _circuit_breakers[service_name]
