"""
Módulo __init__ para resilience

Exporta componentes de resiliência.
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    circuit,
    get_circuit_breaker
)

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    "circuit",
    "get_circuit_breaker"
]
