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
import asyncio
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
from backend.app.config.settings import settings

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
    from backend.application.agents.memory_agent import MemoryAgent
    from backend.application.agents.vectorization_agent import VectorizationAgent
    from backend.infrastructure.adapters.sqlite_memory_adapter import SQLiteMemoryAdapter
    from backend.infrastructure.adapters.sqlserver_memory_adapter import SQLServerMemoryAdapter
    from backend.infrastructure.adapters.sqlserver_pytds_memory_adapter import SQLServerPyTDSMemoryAdapter
    from backend.infrastructure.adapters.duckdb_vector_adapter import DuckDBVectorAdapter
    from backend.app.infrastructure.redis_client import init_redis_client, close_redis_client
    from backend.app.services.image_analysis import ImageAnalysisService
    from backend.app.api.v1.endpoints.memory import set_memory_agent
    from backend.app.api.v1.endpoints.ingest import set_ingest_dependencies
    from backend.app.core.utils.session_manager import SessionManager
    from backend.app.core.retrieval.embedding_backend import get_embedding_backend
    
    MetricsService()
    BillingService()

    runtime_root = Path(settings.RUNTIME_STORAGE_ROOT)
    runtime_root.mkdir(parents=True, exist_ok=True)
    Path(settings.ATTACHMENTS_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.SESSION_LEGACY_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    redis_client = await init_redis_client()
    app.state.redis_client = redis_client
    app.state.redis_enabled = redis_client is not None

    chat_state_backend = settings.CHAT_STATE_BACKEND
    memory_db_path = SessionManager.default_db_path()
    vector_db_path = Path(settings.VECTOR_DB_PATH)
    vector_db_path.parent.mkdir(parents=True, exist_ok=True)

    if chat_state_backend == "sqlserver":
        if not settings.DATABASE_URL:
            raise RuntimeError(
                "CHAT_STATE_BACKEND=sqlserver requires DATABASE_URL configured"
            )
        if str(settings.DATABASE_URL).startswith("mssql+pytds://"):
            memory_repository = SQLServerPyTDSMemoryAdapter(str(settings.DATABASE_URL))
            app.state.chat_state_backend = "sqlserver_pytds"
        else:
            if not settings.USE_SQL_SERVER:
                raise RuntimeError(
                    "Async SQL Server backend requires USE_SQL_SERVER=true"
                )
            from backend.app.config.database import AsyncSessionLocal, engine

            memory_repository = SQLServerMemoryAdapter(
                session_factory=AsyncSessionLocal,
                engine=engine,
            )
            app.state.chat_state_backend = "sqlserver"
    else:
        memory_repository = SQLiteMemoryAdapter(str(memory_db_path))
        app.state.chat_state_backend = "sqlite"

    await memory_repository._ensure_initialized()
    memory_agent = MemoryAgent(memory_repository)
    set_memory_agent(memory_agent)
    app.state.memory_agent = memory_agent
    app.state.memory_db_path = str(memory_db_path)

    vectorization_agent = VectorizationAgent()
    vector_adapter = DuckDBVectorAdapter(str(vector_db_path))
    await vector_adapter._ensure_initialized()
    image_analysis_service = ImageAnalysisService()
    set_ingest_dependencies(vector_adapter, vectorization_agent, image_analysis_service)
    app.state.ingest_vector_adapter = vector_adapter
    app.state.ingest_vectorization_agent = vectorization_agent
    app.state.image_analysis_service = image_analysis_service
    app.state.vector_db_path = str(vector_db_path)

    embedding_backend = get_embedding_backend()
    embedding_ready = False
    if settings.RAG_EMBEDDING_PRELOAD_ON_STARTUP:
        embedding_ready = await asyncio.to_thread(embedding_backend.warm_up, allow_download=False)
        logger.info(
            "embedding_backend_preload",
            model=settings.RAG_EMBEDDING_MODEL,
            ready=embedding_ready,
            local_files_only=settings.RAG_EMBEDDING_LOCAL_FILES_ONLY,
        )
    app.state.embedding_model_ready = embedding_ready
    
    logger.info(
        "services_initialized",
        chat_state_backend=app.state.chat_state_backend,
        memory_db_path=str(memory_db_path),
        vector_db_path=str(vector_db_path),
        redis_enabled=app.state.redis_enabled,
        use_sql_server=settings.USE_SQL_SERVER,
        embedding_model=settings.RAG_EMBEDDING_MODEL,
        embedding_local_files_only=settings.RAG_EMBEDDING_LOCAL_FILES_ONLY,
        embedding_preloaded=bool(getattr(app.state, "embedding_model_ready", False)),
    )
    
    yield
    
    # Shutdown
    await close_redis_client()
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
    
    Use o endpoint `/api/v1/auth/login` para obter um token JWT.
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

from backend.app.api.middleware.auth import AuthMiddleware
from backend.app.api.middleware.tenant import TenantMiddleware
from backend.app.api.middleware.rate_limit import RateLimitMiddleware
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

from backend.app.api.v1.router import api_router as v1_router
from backend.app.api.v2 import router as v2_router

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
        "llm_model": os.getenv("LLM_MODEL_NAME", "unknown"),
        "analytics_source": "parquet",
        "parquet_path": settings.PARQUET_DATA_PATH,
        "chat_state_backend": getattr(app.state, "chat_state_backend", settings.CHAT_STATE_BACKEND),
        "redis_enabled": bool(getattr(app.state, "redis_enabled", settings.REDIS_ENABLED)),
        "embedding_model": settings.RAG_EMBEDDING_MODEL,
        "embedding_local_files_only": settings.RAG_EMBEDDING_LOCAL_FILES_ONLY,
        "embedding_preloaded": bool(getattr(app.state, "embedding_model_ready", False)),
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
    
    # [AJUSTE] Define modo de execucao:
    # - development: ativa auto-reload
    # - production: sem reload
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    if is_dev:
        # [AJUSTE] Polling melhora confiabilidade do file-watch no Windows.
        # Se quiser reduzir uso de CPU, defina WATCHFILES_FORCE_POLLING=false no ambiente.
        os.environ.setdefault("WATCHFILES_FORCE_POLLING", "true")

    # [AJUSTE] HOST/PORT podem ser alterados por variaveis de ambiente.
    # [AJUSTE] reload_dirs/reload_includes controlam o que dispara reinicio automatico.
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=is_dev,
        reload_dirs=["backend"] if is_dev else None,
        reload_includes=["*.py", ".env"] if is_dev else None,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
