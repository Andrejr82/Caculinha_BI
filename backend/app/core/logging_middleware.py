"""
Middleware de Logging para FastAPI
Captura e registra todas as requisições e respostas HTTP
"""
import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging_config import log_api_request, log_api_response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que registra todas as requisições HTTP
    com informações detalhadas e métricas de performance
    """

    def __init__(self, app: ASGIApp, logger_name: str = "agentbi.api"):
        super().__init__(app)
        self.logger = structlog.get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Gera um ID único para a requisição
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extrai informações da requisição
        method = request.method
        url = str(request.url)
        path = request.url.path
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "unknown")

        # Extrai user_id se disponível (do token JWT)
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)

        # Log da requisição
        self.logger.info(
            "request_started",
            request_id=request_id,
            method=method,
            url=url,
            path=path,
            client_host=client_host,
            user_agent=user_agent,
            user_id=user_id,
        )

        # Timestamp de início
        start_time = time.time()

        # Processa a requisição
        try:
            response = await call_next(request)

            # Calcula duração
            duration = time.time() - start_time

            # Log da resposta
            self.logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration=f"{duration:.3f}s",
                duration_ms=f"{duration * 1000:.0f}ms",
                user_id=user_id,
            )

            # Adiciona headers de debug
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration * 1000:.0f}ms"

            return response

        except Exception as exc:
            # Calcula duração até o erro
            duration = time.time() - start_time
            
            # Tratar erros de desconexão/stream de forma graciosa
            error_msg = str(exc)
            if "No response returned" in error_msg or "EndOfStream" in type(exc).__name__:
                self.logger.warning(
                    "client_disconnected",
                    path=path,
                    duration=f"{duration:.3f}s",
                    error=error_msg
                )
                # Não relançar para evitar poluição de logs de erro, pois é um cancelamento do cliente
                return Response(content="Client disconnected", status_code=499)

            # Log do erro
            self.logger.error(
                "request_failed",
                request_id=request_id,
                method=method,
                path=path,
                error=error_msg,
                error_type=type(exc).__name__,
                duration=f"{duration:.3f}s",
                user_id=user_id,
                exc_info=True,
            )

            # Re-lança a exceção para ser tratada pelos handlers
            raise


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que registra métricas de performance
    e identifica requisições lentas
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 1.0,  # segundos
        logger_name: str = "agentbi.performance"
    ):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.logger = structlog.get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # Log de requisições lentas
        if duration > self.slow_request_threshold:
            self.logger.warning(
                "slow_request_detected",
                method=request.method,
                path=request.url.path,
                duration=f"{duration:.3f}s",
                threshold=f"{self.slow_request_threshold}s",
                status_code=response.status_code,
            )

        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que registra eventos de segurança
    como tentativas de autenticação, acessos negados, etc.
    """

    def __init__(self, app: ASGIApp, logger_name: str = "agentbi.security"):
        super().__init__(app)
        self.logger = structlog.get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Paths que devem ser monitorados para segurança
        security_paths = ["/auth", "/login", "/admin"]
        path = request.url.path

        # Verifica se é uma rota de segurança
        is_security_route = any(sec_path in path for sec_path in security_paths)

        response = await call_next(request)

        # Log de eventos de segurança
        if is_security_route:
            client_host = request.client.host if request.client else "unknown"

            # Log de tentativas de autenticação
            if "/auth" in path or "/login" in path:
                if response.status_code == 200:
                    self.logger.info(
                        "authentication_success",
                        path=path,
                        client_host=client_host,
                        user_agent=request.headers.get("user-agent"),
                    )
                elif response.status_code == 401:
                    self.logger.warning(
                        "authentication_failed",
                        path=path,
                        client_host=client_host,
                        user_agent=request.headers.get("user-agent"),
                    )

            # Log de acessos negados
            elif response.status_code == 403:
                self.logger.warning(
                    "access_denied",
                    path=path,
                    client_host=client_host,
                    method=request.method,
                )

            # Log de recursos não encontrados (possível scan)
            elif response.status_code == 404 and "/admin" in path:
                self.logger.warning(
                    "admin_path_not_found",
                    path=path,
                    client_host=client_host,
                    method=request.method,
                )

        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que registra ações de auditoria
    para operações de escrita (POST, PUT, DELETE, PATCH)
    """

    def __init__(self, app: ASGIApp, logger_name: str = "agentbi.audit"):
        super().__init__(app)
        self.logger = structlog.get_logger(logger_name)
        self.audit_methods = {"POST", "PUT", "DELETE", "PATCH"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Só audita métodos de escrita
        if request.method in self.audit_methods:
            path = request.url.path
            client_host = request.client.host if request.client else "unknown"

            # Extrai user_id se disponível
            user_id = None
            if hasattr(request.state, "user"):
                user_id = getattr(request.state.user, "id", None)

            # Processa a requisição
            response = await call_next(request)

            # Log de auditoria
            if response.status_code in [200, 201, 204]:
                self.logger.info(
                    "audit_action",
                    method=request.method,
                    path=path,
                    user_id=user_id,
                    client_host=client_host,
                    status_code=response.status_code,
                    timestamp=time.time(),
                )

            return response
        else:
            return await call_next(request)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que captura e registra todos os erros
    """

    def __init__(self, app: ASGIApp, logger_name: str = "agentbi.errors"):
        super().__init__(app)
        self.logger = structlog.get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)

            # Log de erros HTTP (4xx e 5xx)
            if response.status_code >= 400:
                severity = "error" if response.status_code >= 500 else "warning"

                log_method = getattr(self.logger, severity)
                try:
                    log_method(
                        "http_error",
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code,
                        client_host=request.client.host if request.client else "unknown",
                    )
                except Exception as log_err:
                    # Fallback simple print if structured logging fails
                    print(f"LOGGING ERROR: {log_err} (Original error status: {response.status_code})")

            return response

        except Exception as exc:
            # Log de exceções não tratadas
            self.logger.error(
                "unhandled_exception",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                error_type=type(exc).__name__,
                client_host=request.client.host if request.client else "unknown",
                exc_info=True,
            )
            raise
