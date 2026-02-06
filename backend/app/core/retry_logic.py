"""
Retry Logic com Exponential Backoff
Implementa retry automático para chamadas LLM sem dependências externas

Baseado em melhores práticas 2024-2025 de resiliência
"""

import time
import logging
from typing import Callable, Any, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuração de retry"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        retry_on: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on = retry_on


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calcula delay com exponential backoff"""
    delay = config.initial_delay * (config.exponential_base ** attempt)
    return min(delay, config.max_delay)


def retry_with_backoff(config: RetryConfig = None):
    """
    Decorator para retry com exponential backoff
    
    Usage:
        @retry_with_backoff(RetryConfig(max_attempts=3))
        def call_api():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retry_on as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__} "
                            f"after {delay:.2f}s. Error: {str(e)}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} retry attempts failed for {func.__name__}"
                        )
            
            # Se chegou aqui, todas as tentativas falharam
            raise last_exception
        
        return wrapper
    return decorator


# Configurações pré-definidas
LLM_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=10.0,
    exponential_base=2.0,
    retry_on=(ConnectionError, TimeoutError, Exception)
)

DB_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    initial_delay=1.0,
    max_delay=5.0,
    exponential_base=2.0,
    retry_on=(ConnectionError, TimeoutError)
)


def retry_llm_call(func: Callable) -> Callable:
    """Decorator específico para LLM calls"""
    return retry_with_backoff(LLM_RETRY_CONFIG)(func)


def retry_db_call(func: Callable) -> Callable:
    """Decorator específico para DB calls"""
    return retry_with_backoff(DB_RETRY_CONFIG)(func)
