
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from backend.app.core.observability.context import RequestContext, get_context, set_context
import structlog

logger = structlog.get_logger("observability")

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # 1. Gerar/Extrair Request ID
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        
        # 2. Extrair Tenant ID (Header inicial, será refinado pelo TenantMiddleware depois)
        tenant_id_header = request.headers.get("X-Tenant-Id")
        
        # 3. Inicializar Contexto
        ctx = RequestContext(
            request_id=request_id,
            tenant_id=tenant_id_header
        )
        set_context(ctx)
        
        # 4. Log Inicial
        logger.info(
            "http_request_started",
            method=request.method,
            path=request.url.path,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            # 5. Processar Requisição
            response = await call_next(request)
            
            # 6. Adicionar Header de Resposta
            response.headers["X-Request-Id"] = request_id
            
            # 7. Calcular Duração
            duration = time.time() - start_time
            
            # 8. Log Final com Tenant Atualizado (se Auth/Tenant middleware rodou)
            current_ctx = get_context()
            logger.info(
                "http_request_finished",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_s=round(duration, 4),
                tenant_id=current_ctx.tenant_id
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "http_request_failed",
                error=str(e),
                method=request.method,
                path=request.url.path,
                duration_s=round(duration, 4),
                exc_info=True
            )
            raise e
