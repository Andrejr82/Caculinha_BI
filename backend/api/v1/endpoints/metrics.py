
from fastapi import APIRouter, Response
from backend.app.core.observability.metrics import get_metrics_content, CONTENT_TYPE_LATEST

router = APIRouter()

@router.get("/metrics")
async def metrics():
    """
    Exposes Prometheus metrics for scraping.
    """
    data, content_type = get_metrics_content()
    return Response(content=data, media_type=content_type)
