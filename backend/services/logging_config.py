"""
Logging Configuration - Configuração de Logs Estruturados

Configura structlog para logs estruturados em JSON.

Uso:
    from backend.services import setup_logging
    setup_logging()

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
import sys
import logging
from pathlib import Path

import structlog


def setup_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    log_file: str = None,
):
    """
    Configura logging estruturado para a aplicação.
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        json_format: Se True, logs em JSON; se False, formato legível
        log_file: Arquivo opcional para persistir logs
    """
    # Determinar nível
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar processadores do structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_format:
        # Formato JSON para produção
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Formato legível para desenvolvimento
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    
    # Configurar structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging padrão do Python
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    
    # Silenciar logs verbosos de bibliotecas
    for logger_name in ["httpx", "httpcore", "urllib3", "asyncio"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Configurar arquivo de log se especificado
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        logging.getLogger().addHandler(file_handler)
    
    logger = structlog.get_logger(__name__)
    logger.info(
        "logging_configured",
        level=log_level,
        json_format=json_format,
        log_file=log_file,
    )


def get_logger(name: str = None):
    """
    Retorna um logger configurado.
    
    Args:
        name: Nome do módulo (usa __name__ se não fornecido)
    
    Returns:
        Logger estruturado
    """
    return structlog.get_logger(name)


# Contexto de request para logs
def bind_request_context(
    request_id: str,
    tenant_id: str = None,
    user_id: str = None,
):
    """
    Vincula contexto de request aos logs.
    
    Uso no middleware:
        bind_request_context(request_id="abc", tenant_id="xyz")
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        tenant_id=tenant_id,
        user_id=user_id,
    )


def clear_request_context():
    """Limpa contexto de request dos logs."""
    structlog.contextvars.clear_contextvars()
