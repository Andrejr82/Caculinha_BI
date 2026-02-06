"""
FastAPI Main Application
Entry point for the backend API
"""

from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.config.database import engine
from app.config.settings import get_settings
from app.infrastructure.database.models import Base
from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter, DuckDBEnhancedAdapter

# Import logging configuration
from app.core.logging_config import setup_application_logging
from app.core.logging_middleware import (
    RequestLoggingMiddleware,
    PerformanceLoggingMiddleware,
    SecurityLoggingMiddleware,
    AuditLoggingMiddleware,
    ErrorLoggingMiddleware,
)

settings = get_settings()

# Setup complete logging system
loggers = setup_application_logging(environment=settings.ENVIRONMENT)

# Get main logger
logger = structlog.get_logger("agentbi")
api_logger = logging.getLogger("agentbi.api")
security_logger = logging.getLogger("agentbi.security")
chat_logger = logging.getLogger("agentbi.chat")
audit_logger = logging.getLogger("agentbi.audit")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("application_startup", environment=settings.ENVIRONMENT)
    
    # 🛠️ FIX: Create tables for BOTH SQL Server AND SQLite fallback
    try:
        if settings.DEBUG:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            if settings.USE_SQL_SERVER:
                logger.info("database_tables_created", db="SQL Server")
            else:
                logger.info("database_tables_created", db="SQLite (local)")
    except Exception as e:
        logger.warning("database_connection_failed", error=str(e))
        logger.info("continuing_without_database")

    try:
        # Initialize DuckDBEnhancedAdapter (singleton)
        logger.info("initializing_data_adapter")
        app.state.data_adapter = get_duckdb_adapter()
        logger.info("data_adapter_initialized", adapter_type="DuckDBEnhanced")
    except Exception as e:
        logger.warning("data_adapter_failed", error=str(e))
        logger.info("continuing_without_data_adapter")
    
    # ✅ PERFORMANCE FIX: Background Initialization of Agents
    # Starts immediately but doesn't block the server from accepting connections.
    from app.api.v1.endpoints.chat import initialize_agents_async
    import asyncio
    
    # Schedule the initialization task
    # We use create_task to run it in the background event loop
    asyncio.create_task(initialize_agents_async())
    logger.info("startup_background_task_scheduled: Agent initialization")

    yield
    
    # Shutdown
    logger.info("application_shutdown")
    if hasattr(app.state, "data_adapter"):
        try:
            await app.state.data_adapter.disconnect()
        except:
            pass
    try:
        await engine.dispose()
    except:
        pass



# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configure CORS
origins = settings.BACKEND_CORS_ORIGINS.split(",") if isinstance(settings.BACKEND_CORS_ORIGINS, str) else settings.BACKEND_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use configured origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middlewares
# app.add_middleware(ErrorLoggingMiddleware)
# app.add_middleware(AuditLoggingMiddleware)
# app.add_middleware(SecurityLoggingMiddleware)
# app.add_middleware(PerformanceLoggingMiddleware, slow_request_threshold=2.0)
# app.add_middleware(RequestLoggingMiddleware)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Root endpoint for simple login UI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render a basic login page"""
    return templates.TemplateResponse("login.html", {"request": request})


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if not settings.DEBUG else str(exc)
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

 
