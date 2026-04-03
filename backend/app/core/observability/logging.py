import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

import structlog

from backend.app.core.observability.context import get_context

DEFAULT_LOG_DIR = Path("backend/logs")


class _LoggerPrefixFilter(logging.Filter):
    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith(self.prefix)


class _ExcludeLoggerPrefixFilter(logging.Filter):
    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith(self.prefix)


def inject_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Injeta IDs do RequestContext nos logs."""
    ctx = get_context()
    if ctx.request_id:
        event_dict["request_id"] = ctx.request_id
    if ctx.tenant_id:
        event_dict["tenant_id"] = ctx.tenant_id
    if ctx.user_id:
        event_dict["user_id"] = ctx.user_id
    if ctx.trace_id:
        event_dict["trace_id"] = ctx.trace_id
    if ctx.span_id:
        event_dict["span_id"] = ctx.span_id
    return event_dict


def _resolve_level(log_level: str) -> int:
    return getattr(logging, str(log_level).upper(), logging.INFO)


def _build_formatter(
    log_format: str,
    shared_processors: list[structlog.typing.Processor],
) -> structlog.stdlib.ProcessorFormatter:
    renderer = (
        structlog.dev.ConsoleRenderer(colors=True)
        if log_format == "console"
        else structlog.processors.JSONRenderer()
    )
    return structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )


def configure_logging(log_level: str = "INFO") -> None:
    level = _resolve_level(log_level)
    log_format = os.getenv("LOG_FORMAT", "json").strip().lower()
    if log_format not in {"json", "console"}:
        log_format = "json"

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        inject_context,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = _build_formatter(log_format, shared_processors)
    handlers: list[logging.Handler] = []

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    handlers.append(stream_handler)

    log_dir = Path(os.getenv("LOG_DIR", str(DEFAULT_LOG_DIR)))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)

        backend_file_handler = RotatingFileHandler(
            filename=log_dir / "backend.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        backend_file_handler.setFormatter(formatter)
        backend_file_handler.addFilter(_ExcludeLoggerPrefixFilter("agentbi.frontend"))
        handlers.append(backend_file_handler)

        frontend_file_handler = RotatingFileHandler(
            filename=log_dir / "frontend.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        frontend_file_handler.setFormatter(formatter)
        frontend_file_handler.addFilter(_LoggerPrefixFilter("agentbi.frontend"))
        handlers.append(frontend_file_handler)
    except Exception:
        # Se falhar criação de arquivo, mantém logging em stdout.
        pass

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )

    for noisy_logger in (
        "httpx",
        "httpcore",
        "urllib3",
        "asyncio",
        "pytds",
        "faiss",
        "sentence_transformers",
        "huggingface_hub",
        "transformers",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(level)

    logging.captureWarnings(True)

    structlog.get_logger(__name__).info(
        "logging_configured",
        log_level=logging.getLevelName(level),
        log_format=log_format,
        log_dir=str(log_dir),
        frontend_log_file="frontend.log",
    )
