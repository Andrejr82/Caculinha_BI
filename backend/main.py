"""
Caculinha BI Agent Platform - Main Application

Ponto de entrada da aplicação FastAPI com configuração completa
de middlewares, routers e serviços.

Uso:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

# Carregar .env
from dotenv import load_dotenv
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

# Configurar logging (Observability)
from backend.app.core.observability.logging import configure_logging
configure_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))

logger = structlog.get_logger(__name__)


# =============================================================================
# LIFESPAN (Startup/Shutdown)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    # Startup
    logger.info(
        "application_starting",
        env=os.getenv("ENVIRONMENT", "development"),
        version="2.0.0",
    )
    
    # Inicializar serviços
    from backend.services.metrics import MetricsService
    from backend.services.billing import BillingService
    
    MetricsService()
    BillingService()
    
    logger.info("services_initialized")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")


# =============================================================================
# APPLICATION
# =============================================================================

app = FastAPI(
    title="Caculinha BI Agent Platform",
    description="""
    Plataforma de BI Conversacional com Agentes de IA.
    
    ## Features
    
    * **Chat Conversacional**: Pergunte em linguagem natural sobre seus dados
    * **8 Agentes Especializados**: SQL, Insight, Forecast, Metadata, Tenant, Security, Monitoring
    * **Multi-Tenancy**: Suporte a múltiplas organizações
    * **Rate Limiting**: Controle de uso por plano
    * **Observabilidade**: Métricas e logs estruturados
    
    ## Autenticação
    
    Use o endpoint `/api/v2/auth/login` para obter um token JWT.
    Inclua o token no header `Authorization: Bearer <token>`.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# =============================================================================
# CORS
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# MIDDLEWARES CUSTOMIZADOS
# =============================================================================

from backend.api.middleware.auth import AuthMiddleware
from backend.api.middleware.tenant import TenantMiddleware
from backend.api.middleware.rate_limit import RateLimitMiddleware
from backend.app.core.observability.middleware import ObservabilityMiddleware

# Ordem de execução (Request):
# 1. Observability (Start Timer, Request ID)
# 2. CORS
# 3. Rate Limit
# 4. Tenant (Resolve Tenant)
# 5. Auth (Resolve User)

# Em FastAPI/Starlette, o middleware adicionado POR ÚLTIMO é executado PRIMEIRO na entrada.
app.add_middleware(AuthMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ObservabilityMiddleware) # Envolve todos os outros


# =============================================================================
# ROUTERS
# =============================================================================

from backend.api.v1.router import api_router as v1_router
from backend.api.v2 import router as v2_router

app.include_router(v1_router) # Já tem prefixo /api/v1 no router
app.include_router(v2_router, prefix="/api/v2")


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "name": "Caculinha BI Agent Platform",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api/v2",
    }


@app.get("/ping")
async def ping():
    """Endpoint de ping para load balancers."""
    return {"status": "pong"}


@app.get("/health")
async def health():
    """Endpoint de saúde para orquestração (Docker/K8s)."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "llm_model": os.getenv("LLM_MODEL_NAME", "unknown")
    }


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=exc,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        }
    )


# =============================================================================
# ENTRYPOINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
