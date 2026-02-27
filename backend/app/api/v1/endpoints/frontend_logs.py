"""
Endpoint para receber logs do frontend
Permite que o frontend envie logs importantes para análise
"""
import logging
from typing import List, Any, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ConfigDict
import structlog

from backend.app.core.observability.context import get_context

router = APIRouter(tags=["logs"])

# Logger específico para logs do frontend
frontend_logger = structlog.get_logger("agentbi.frontend")


class FrontendLogEntry(BaseModel):
    """Modelo para entrada de log do frontend"""
    timestamp: str
    level: int
    levelName: str = Field(..., alias="levelName")
    message: str
    context: Dict[str, Any] | None = None
    error: Dict[str, Any] | None = None
    user: Dict[str, Any] | None = None
    session: Dict[str, Any] | None = None
    page: Dict[str, Any] | None = None
    browser: Dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class FrontendLogsRequest(BaseModel):
    """Request contendo múltiplos logs do frontend"""
    logs: List[FrontendLogEntry]


def map_frontend_log_level(level: int) -> int:
    """
    Mapeia níveis de log do frontend para níveis do Python logging
    Frontend: DEBUG=0, INFO=1, WARN=2, ERROR=3, CRITICAL=4
    Python: DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50
    """
    mapping = {
        0: logging.DEBUG,      # DEBUG
        1: logging.INFO,       # INFO
        2: logging.WARNING,    # WARN
        3: logging.ERROR,      # ERROR
        4: logging.CRITICAL,   # CRITICAL
    }
    return mapping.get(level, logging.INFO)


@router.post("/logs", status_code=202)
async def receive_frontend_logs(
    request: Request,
    logs_request: FrontendLogsRequest
) -> dict:
    """
    Recebe e processa logs do frontend

    - **logs**: Lista de entradas de log do frontend

    Retorna um status 202 (Accepted) indicando que os logs foram recebidos
    """
    try:
        logs_received = len(logs_request.logs)
        ctx = get_context()
        client_ip = request.client.host if request.client else None

        # Processa cada log
        for log_entry in logs_request.logs:
            python_level = map_frontend_log_level(log_entry.level)

            event_data: dict[str, Any] = {
                "source": "frontend",
                "frontend_timestamp": log_entry.timestamp,
                "frontend_level_name": log_entry.levelName,
                "frontend_message": log_entry.message,
                "client_ip": client_ip,
                "path": str(request.url.path),
                "request_id": ctx.request_id,
            }

            if log_entry.context:
                event_data["context"] = log_entry.context

            if log_entry.user:
                event_data["frontend_user_id"] = log_entry.user.get("id")
                event_data["frontend_user_email"] = log_entry.user.get("email")

            if log_entry.session:
                event_data["session_id"] = log_entry.session.get("id")
                event_data["session_duration"] = log_entry.session.get("duration")

            if log_entry.page:
                event_data["page_url"] = log_entry.page.get("url")
                event_data["page_title"] = log_entry.page.get("title")
                event_data["page_referrer"] = log_entry.page.get("referrer")

            if log_entry.browser:
                event_data["user_agent"] = log_entry.browser.get("userAgent")
                event_data["browser_language"] = log_entry.browser.get("language")
                event_data["browser_platform"] = log_entry.browser.get("platform")

            if log_entry.error:
                event_data["error"] = log_entry.error

            if python_level >= logging.CRITICAL:
                frontend_logger.critical("frontend_log", **event_data)
            elif python_level >= logging.ERROR:
                frontend_logger.error("frontend_log", **event_data)
            elif python_level >= logging.WARNING:
                frontend_logger.warning("frontend_log", **event_data)
            elif python_level >= logging.INFO:
                frontend_logger.info("frontend_log", **event_data)
            else:
                frontend_logger.debug("frontend_log", **event_data)

        frontend_logger.info(
            "frontend_logs_batch_received",
            source="frontend",
            logs_received=logs_received,
            client_ip=client_ip,
            path=str(request.url.path),
            request_id=ctx.request_id,
        )

        return {
            "status": "accepted",
            "logs_received": logs_received,
            "request_id": ctx.request_id,
            "message": f"Successfully received {logs_received} log(s) from frontend",
        }

    except Exception as e:
        frontend_logger.error(
            "frontend_logs_processing_failed",
            error=str(e),
            path=str(request.url.path),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error processing logs: {str(e)}"
        )


@router.get("/logs/health")
async def logs_health_check() -> dict:
    """
    Health check endpoint para o sistema de logs
    """
    return {
        "status": "healthy",
        "service": "frontend-logs",
        "timestamp": datetime.utcnow().isoformat()
    }
