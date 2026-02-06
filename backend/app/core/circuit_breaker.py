"""
Circuit Breaker para LLM Calls
Implementa pattern de Circuit Breaker para evitar chamadas repetidas a serviços falhando

Baseado em melhores práticas 2024-2025 de resiliência em sistemas LLM
"""

import logging
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


class CircuitBreakerState:
    """Estados do Circuit Breaker"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker simples sem dependências externas
    
    Estados:
    - CLOSED: Funcionamento normal
    - OPEN: Bloqueando chamadas (após muitas falhas)
    - HALF_OPEN: Testando recuperação
    """
    
    def __init__(
        self,
        name: str,
        fail_max: int = 5,
        timeout_duration: int = 60,
        success_threshold: int = 2
    ):
        self.name = name
        self.fail_max = fail_max
        self.timeout_duration = timeout_duration
        self.success_threshold = success_threshold
        
        self.fail_counter = 0
        self.success_counter = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executa função com circuit breaker"""
        
        # Se OPEN, verificar se deve tentar novamente
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Service unavailable. Try again in {self.timeout_duration}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar resetar o circuit breaker"""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout_duration
    
    def _on_success(self):
        """Chamado quando a função executa com sucesso"""
        self.fail_counter = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_counter += 1
            if self.success_counter >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.success_counter = 0
                logger.info(f"Circuit breaker {self.name} CLOSED (recovered)")
    
    def _on_failure(self):
        """Chamado quando a função falha"""
        self.fail_counter += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker {self.name} back to OPEN (recovery failed)")
        elif self.fail_counter >= self.fail_max:
            self.state = CircuitBreakerState.OPEN
            logger.error(
                f"Circuit breaker {self.name} OPENED after {self.fail_counter} failures"
            )
    
    def get_status(self) -> dict:
        """Retorna status atual do circuit breaker"""
        return {
            "name": self.name,
            "state": self.state,
            "fail_counter": self.fail_counter,
            "success_counter": self.success_counter,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class CircuitBreakerError(Exception):
    """Exceção lançada quando circuit breaker está aberto"""
    pass


# Circuit Breakers globais
gemini_breaker = CircuitBreaker(
    name="gemini",
    fail_max=5,
    timeout_duration=60,
    success_threshold=2
)

groq_breaker = CircuitBreaker(
    name="groq",
    fail_max=5,
    timeout_duration=60,
    success_threshold=2
)

sql_server_breaker = CircuitBreaker(
    name="sql_server",
    fail_max=3,
    timeout_duration=30,
    success_threshold=2
)


def with_circuit_breaker(breaker: CircuitBreaker):
    """
    Decorator para aplicar circuit breaker a uma função
    
    Usage:
        @with_circuit_breaker(gemini_breaker)
        def call_gemini_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def get_all_circuit_breakers_status() -> dict:
    """Retorna status de todos os circuit breakers"""
    return {
        "gemini": gemini_breaker.get_status(),
        "groq": groq_breaker.get_status(),
        "sql_server": sql_server_breaker.get_status()
    }
