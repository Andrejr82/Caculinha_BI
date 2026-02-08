"""
Endpoint para receber logs do frontend
Permite que o frontend envie logs importantes para análise
"""
import logging
from typing import List, Any, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ConfigDict

from backend.app.core.logging_config import log_api_request

router = APIRouter(tags=["logs"])

# Logger específico para logs do frontend
frontend_logger = logging.getLogger("agentbi.frontend")


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

        # Processa cada log
        for log_entry in logs_request.logs:
            # Mapeia o nível do log
            python_level = map_frontend_log_level(log_entry.level)

            # Prepara dados extras para o log
            extra = {
                "source": "frontend",
                "frontend_timestamp": log_entry.timestamp,
            }

            # Adiciona contexto se disponível
            if log_entry.context:
                extra["context"] = log_entry.context

            # Adiciona informações do usuário
            if log_entry.user:
                extra["user_id"] = log_entry.user.get("id")
                extra["user_email"] = log_entry.user.get("email")

            # Adiciona informações da sessão
            if log_entry.session:
                extra["session_id"] = log_entry.session.get("id")
                extra["session_duration"] = log_entry.session.get("duration")

            # Adiciona informações da página
            if log_entry.page:
                extra["page_url"] = log_entry.page.get("url")
                extra["page_title"] = log_entry.page.get("title")

            # Adiciona informações do browser
            if log_entry.browser:
                extra["user_agent"] = log_entry.browser.get("userAgent")
                extra["browser_language"] = log_entry.browser.get("language")
                extra["browser_platform"] = log_entry.browser.get("platform")

            # Adiciona informações de erro se disponível
            error_info = None
            if log_entry.error:
                error_info = (
                    f"{log_entry.error.get('name', 'Error')}: "
                    f"{log_entry.error.get('message', 'Unknown error')}"
                )
                if log_entry.error.get("stack"):
                    error_info += f"\n{log_entry.error.get('stack')}"
                extra["error"] = error_info

            # Registra o log
            message = f"[Frontend] {log_entry.message}"
            if error_info:
                message += f" - {error_info}"

            frontend_logger.log(
                python_level,
                message,
                extra=extra
            )

        return {
            "status": "accepted",
            "logs_received": logs_received,
            "message": f"Successfully received {logs_received} log(s) from frontend"
        }

    except Exception as e:
        frontend_logger.error(
            f"Error processing frontend logs: {str(e)}",
            exc_info=True
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
