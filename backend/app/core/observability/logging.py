
import logging
import sys
import structlog
from typing import Any, Dict
from pathlib import Path
from logging.handlers import RotatingFileHandler
from backend.app.core.observability.context import get_context

def inject_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Injeta IDs do RequestContext nos logs."""
    ctx = get_context()
    if ctx.request_id:
        event_dict["request_id"] = ctx.request_id
    if ctx.tenant_id:
        event_dict["tenant_id"] = ctx.tenant_id
    return event_dict

def configure_logging(log_level="INFO"):
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        inject_context,
        structlog.processors.JSONRenderer()
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Redirecionar logs da standard library para o structlog + persistir em arquivo.
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    try:
        log_dir = Path("backend/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=log_dir / "backend.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        handlers.append(file_handler)
    except Exception:
        # Se falhar criação de arquivo, mantém logging em stdout.
        pass

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers,
        force=True,
    )
