"""
Health Check Endpoint with Timeout
Provides system health status with configurable timeout
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
import structlog

from app.config.settings import get_settings

router = APIRouter()
logger = structlog.get_logger("agentbi.health")
settings = get_settings()

# Health check configuration
HEALTH_CHECK_TIMEOUT = 5  # seconds
DEPENDENCY_CHECK_INTERVAL = 30  # cache health status for 30 seconds

# Cache for health status
_last_health_check: Dict[str, Any] = {
    "timestamp": 0,
    "status": None
}


@router.get("/health", tags=["health"], status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint with timeout protection

    Returns:
        - status: healthy/degraded/unhealthy
        - version: application version
        - environment: current environment
        - timestamp: current timestamp
        - checks: detailed health checks for each component

    Raises:
        503 Service Unavailable if health check times out
    """
    try:
        # Use cached health status if fresh (< 30 seconds old)
        current_time = time.time()
        if (_last_health_check["status"] and
            current_time - _last_health_check["timestamp"] < DEPENDENCY_CHECK_INTERVAL):
            logger.debug("health_check_cached", age=current_time - _last_health_check["timestamp"])
            return _last_health_check["status"]

        # Perform health check with timeout
        health_status = await asyncio.wait_for(
            check_dependencies(),
            timeout=HEALTH_CHECK_TIMEOUT
        )

        # Update cache
        _last_health_check["timestamp"] = current_time
        _last_health_check["status"] = health_status

        logger.info("health_check_success", status=health_status["status"])
        return health_status

    except asyncio.TimeoutError:
        logger.error("health_check_timeout", timeout=HEALTH_CHECK_TIMEOUT)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check timeout after {HEALTH_CHECK_TIMEOUT}s"
        )
    except Exception as e:
        logger.error("health_check_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


async def check_dependencies() -> Dict[str, Any]:
    """
    Check health of all system dependencies

    Returns:
        Dictionary with overall status and individual component checks
    """
    checks = {}
    overall_status = "healthy"

    # Check 1: Database connectivity (if enabled)
    if settings.USE_SQL_SERVER:
        db_check = await check_database()
        checks["database"] = db_check
        if db_check["status"] != "healthy":
            overall_status = "degraded"
    else:
        checks["database"] = {
            "status": "disabled",
            "message": "SQL Server disabled, using Parquet fallback"
        }

    # Check 2: Data adapter (Parquet/Hybrid)
    data_check = await check_data_adapter()
    checks["data_adapter"] = data_check
    if data_check["status"] != "healthy":
        overall_status = "degraded"

    # Check 3: Environment configuration
    env_check = check_environment()
    checks["environment"] = env_check
    if env_check["status"] != "healthy":
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


async def check_database() -> Dict[str, Any]:
    """
    Check database connectivity with timeout

    Returns:
        Status dictionary for database
    """
    try:
        from app.config.database import engine

        # Try to connect with short timeout
        async with asyncio.timeout(2):
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")

        return {
            "status": "healthy",
            "message": "Database connected"
        }
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "message": "Database timeout"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }


async def check_data_adapter() -> Dict[str, Any]:
    """
    Check data adapter (Parquet/Hybrid) status

    Returns:
        Status dictionary for data adapter
    """
    try:
        from pathlib import Path

        # Check if Parquet file exists
        parquet_path = Path(settings.PARQUET_DATA_PATH)
        if parquet_path.exists():
            return {
                "status": "healthy",
                "source": "parquet",
                "message": f"Parquet file accessible: {parquet_path.name}"
            }
        else:
            return {
                "status": "unhealthy",
                "source": "parquet",
                "message": f"Parquet file not found: {settings.PARQUET_DATA_PATH}"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Data adapter error: {str(e)}"
        }


def check_environment() -> Dict[str, Any]:
    """
    Check critical environment variables

    Returns:
        Status dictionary for environment configuration
    """
    try:
        issues = []

        # Check SECRET_KEY
        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
            issues.append("SECRET_KEY too short")

        # Check GEMINI_API_KEY (if needed for AI features)
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "sua_chave_api_gemini_aqui":
            issues.append("GEMINI_API_KEY not configured")

        if issues:
            return {
                "status": "degraded",
                "message": f"Environment issues: {', '.join(issues)}"
            }

        return {
            "status": "healthy",
            "message": "Environment configured"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Environment check error: {str(e)}"
        }


@router.get("/health/live", tags=["health"], status_code=status.HTTP_200_OK)
async def liveness_probe():
    """
    Kubernetes liveness probe - checks if app is running

    Returns:
        Simple status response
    """
    return {"status": "alive"}


@router.get("/health/ready", tags=["health"], status_code=status.HTTP_200_OK)
async def readiness_probe():
    """
    Kubernetes readiness probe - checks if app is ready to serve traffic

    Returns:
        Ready status if all critical dependencies are available

    Raises:
        503 if not ready
    """
    try:
        # Quick check of critical dependencies only
        health = await asyncio.wait_for(check_dependencies(), timeout=3)

        if health["status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )

        return {"status": "ready"}
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Readiness check timeout"
        )
