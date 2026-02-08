
import logging
import sys
import structlog
from typing import Any, Dict
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
    
    # Redirecionar logs da standard library para o structlog
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)
