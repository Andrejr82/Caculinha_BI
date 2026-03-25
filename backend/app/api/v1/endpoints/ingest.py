"""
Ingest Endpoint — API de Ingestão de Documentos

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
import structlog

from backend.app.api.dependencies import get_current_active_user
from backend.app.core.chat_capabilities import require_chat_capability
from backend.app.infrastructure.database.models import User
from backend.domain.entities.document import Document
from backend.app.core.security.content_safety import (
    contains_dangerous_text_payload,
    validate_upload_filename,
)
from backend.app.infrastructure.runtime_lock import runtime_lock
from backend.app.services.image_analysis import ImageAnalysisService
from backend.services.metrics import MetricsService
from backend.app.services.audit_log import get_audit_logger, AuditAction

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["Ingest"])

MAX_INGEST_FILE_BYTES = 2 * 1024 * 1024
MAX_INGEST_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_INGEST_EXTENSIONS = {
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".csv": {"text/csv", "text/plain", "application/vnd.ms-excel", "application/octet-stream"},
    ".tsv": {"text/tab-separated-values", "text/plain", "application/octet-stream"},
    ".json": {"application/json", "text/plain", "application/octet-stream"},
    ".log": {"text/plain", "application/octet-stream"},
    ".xml": {"application/xml", "text/xml", "text/plain", "application/octet-stream"},
}
ALLOWED_IMAGE_EXTENSIONS = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
}


class IngestRequest(BaseModel):
    """Request para ingestão de texto."""
    content: str = Field(..., min_length=1)
    source: str = "manual"
    metadata: Optional[dict] = None


class IngestResponse(BaseModel):
    """Response da ingestão."""
    document_ids: List[str]
    chunks_count: int
    success: bool = True
    analysis_summary: Optional[str] = None


# Placeholder para adapters (injetados via dependency)
_vector_adapter = None
_vectorization_agent = None
_image_analysis_service = None


def set_ingest_dependencies(
    vector_adapter,
    vectorization_agent,
    image_analysis_service: Optional[ImageAnalysisService] = None,
):
    """Configura dependências (chamado no startup)."""
    global _vector_adapter, _vectorization_agent, _image_analysis_service
    _vector_adapter = vector_adapter
    _vectorization_agent = vectorization_agent
    _image_analysis_service = image_analysis_service


def _require_ingest_dependencies():
    if _vector_adapter is None or _vectorization_agent is None:
        raise HTTPException(status_code=503, detail="Ingest service not initialized")


def _require_image_analysis_service():
    if _image_analysis_service is None:
        raise HTTPException(status_code=503, detail="Image analysis service not initialized")


def _record_media_event(
    *,
    media_type: str,
    status: str,
    filename: str,
    session_id: str,
    current_user: User,
    content_size: int = 0,
    error_message: Optional[str] = None,
) -> None:
    metrics = MetricsService()
    metrics.increment("chat_media_upload_total", labels={"media_type": media_type, "status": status})
    if content_size > 0 and status == "accepted":
        metrics.increment("chat_media_bytes_total", value=content_size, labels={"media_type": media_type})

    get_audit_logger().log_action(
        action=AuditAction.DATA_WRITE,
        user_id=str(getattr(current_user, "id", "") or ""),
        username=str(getattr(current_user, "username", "") or ""),
        success=status == "accepted",
        error_message=error_message,
        details={
            "media_type": media_type,
            "status": status,
            "filename": filename,
            "session_id": session_id or None,
            "content_size": content_size,
        },
    )


def _validate_ingest_upload(file: UploadFile, content: bytes) -> None:
    filename = file.filename or "upload.txt"
    validate_upload_filename(filename)
    suffix = Path(filename).suffix.lower()
    content_type = str(file.content_type or "application/octet-stream").lower()

    if suffix not in ALLOWED_INGEST_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Tipo de arquivo não suportado para ingestão")

    if content_type not in ALLOWED_INGEST_EXTENSIONS[suffix]:
        raise HTTPException(status_code=415, detail="Content-Type incompatível com o tipo de arquivo")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio não pode ser ingerido")

    if len(content) > MAX_INGEST_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite de 2 MB")

    if b"\x00" in content:
        raise HTTPException(status_code=400, detail="Arquivo binário não suportado para ingestão textual")


def _validate_image_upload(file: UploadFile, content: bytes) -> None:
    filename = file.filename or "upload.png"
    validate_upload_filename(filename)
    suffix = Path(filename).suffix.lower()
    content_type = str(file.content_type or "").lower()

    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Tipo de imagem não suportado para análise")

    if content_type not in ALLOWED_IMAGE_EXTENSIONS[suffix]:
        raise HTTPException(status_code=415, detail="Content-Type incompatível com a imagem enviada")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Imagem vazia não pode ser analisada")

    if len(content) > MAX_INGEST_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Imagem excede o limite de 5 MB")


@router.post("", response_model=IngestResponse)
async def ingest_text(
    request: IngestRequest,
    current_user: User = Depends(get_current_active_user),
    tenant_id: str = "default",
):
    """
    Ingere texto como documento para RAG.
    
    Pipeline:
    1. Divide em chunks
    2. Gera embeddings
    3. Indexa no vector store
    """
    _require_ingest_dependencies()
    require_chat_capability(current_user, "attachments")
    logger.info("ingest_request", content_len=len(request.content), tenant_id=tenant_id)
    
    try:
        metadata = dict(request.metadata or {})
        if contains_dangerous_text_payload(request.content):
            raise HTTPException(status_code=400, detail="Conteúdo ativo não suportado para ingestão")
        metadata.setdefault("uploaded_by", str(getattr(current_user, "id", "")))
        metadata.setdefault("uploader_role", str(getattr(current_user, "role", "")))
        metadata.setdefault("source", request.source)
        lock_scope = str(
            metadata.get("session_id")
            or metadata.get("filename")
            or metadata.get("uploaded_by")
            or "manual"
        ).strip() or "manual"

        async with runtime_lock(f"ingest:{tenant_id}:{lock_scope}", ttl_seconds=45, wait_timeout_seconds=1.5) as acquired:
            if not acquired:
                raise HTTPException(status_code=409, detail="Outra ingestão já está em andamento para este contexto")

            # Cria chunks do documento
            chunks = Document.create_chunks(
                tenant_id=tenant_id,
                content=request.content,
                chunk_size=512,
                source=request.source,
                metadata=metadata,
            )
            
            document_ids = []
            
            for chunk in chunks:
                # Gera embedding
                embedding = None
                if _vectorization_agent:
                    embedding_vec = await _vectorization_agent.embed_text(chunk.content)
                    if embedding_vec:
                        embedding = _vectorization_agent.create_embedding_entity(chunk.id, embedding_vec)
                
                # Indexa no vector store
                if _vector_adapter and embedding:
                    await _vector_adapter.index_document(chunk, embedding)
                
                document_ids.append(chunk.id)
            
            logger.info("ingest_complete", chunks=len(chunks), tenant_id=tenant_id, lock_scope=lock_scope)
            
            return IngestResponse(
                document_ids=document_ids,
                chunks_count=len(chunks),
                success=True,
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ingest_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    tenant_id: str = Form("default"),
    session_id: str = Form(""),
    current_user: User = Depends(get_current_active_user),
):
    """Ingere arquivo (TXT, CSV, etc)."""
    _require_ingest_dependencies()
    require_chat_capability(current_user, "attachments")
    normalized_session_id = str(session_id or "").strip()
    logger.info(
        "ingest_file",
        filename=file.filename,
        tenant_id=tenant_id,
        session_id=normalized_session_id or None,
    )
    
    try:
        content = await file.read()
        _validate_ingest_upload(file, content)
        text = content.decode("utf-8")
        if not text.strip():
            raise HTTPException(status_code=400, detail="Arquivo sem conteúdo textual útil")
        if contains_dangerous_text_payload(text):
            raise HTTPException(status_code=400, detail="Conteúdo ativo não suportado para ingestão")

        request = IngestRequest(
            content=text,
            source="manual",
            metadata={
                "filename": file.filename or "upload.txt",
                "content_type": file.content_type or "text/plain",
                "session_id": normalized_session_id or None,
                "uploaded_via": "chat_attachment" if normalized_session_id else "manual_upload",
            },
        )
        response = await ingest_text(request, current_user=current_user, tenant_id=tenant_id)
        _record_media_event(
            media_type="document",
            status="accepted",
            filename=file.filename or "upload.txt",
            session_id=normalized_session_id,
            current_user=current_user,
            content_size=len(content),
        )
        return response
    
    except UnicodeDecodeError:
        _record_media_event(
            media_type="document",
            status="rejected",
            filename=file.filename or "upload.txt",
            session_id=normalized_session_id,
            current_user=current_user,
            error_message="invalid_utf8",
        )
        raise HTTPException(status_code=400, detail="Arquivo deve ser texto UTF-8")
    except HTTPException:
        _record_media_event(
            media_type="document",
            status="rejected",
            filename=file.filename or "upload.txt",
            session_id=normalized_session_id,
            current_user=current_user,
            error_message="http_exception",
        )
        raise
    except Exception as e:
        logger.error("ingest_file_error", error=str(e))
        _record_media_event(
            media_type="document",
            status="rejected",
            filename=file.filename or "upload.txt",
            session_id=normalized_session_id,
            current_user=current_user,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image", response_model=IngestResponse)
async def ingest_image(
    file: UploadFile = File(...),
    tenant_id: str = Form("default"),
    session_id: str = Form(""),
    analysis_prompt: str = Form(""),
    current_user: User = Depends(get_current_active_user),
):
    """Analisa imagem e indexa o resultado textual para uso em RAG."""
    _require_ingest_dependencies()
    _require_image_analysis_service()
    require_chat_capability(current_user, "attachments")
    normalized_session_id = str(session_id or "").strip()
    logger.info(
        "ingest_image",
        filename=file.filename,
        tenant_id=tenant_id,
        session_id=normalized_session_id or None,
    )

    try:
        content = await file.read()
        _validate_image_upload(file, content)

        analysis_result = await _image_analysis_service.analyze_image(
            image_bytes=content,
            mime_type=str(file.content_type or "image/png"),
            filename=file.filename or "imagem.png",
            prompt=analysis_prompt,
        )

        request = IngestRequest(
            content=analysis_result.summary,
            source="manual",
            metadata={
                "filename": file.filename or "imagem.png",
                "content_type": file.content_type or "image/png",
                "session_id": normalized_session_id or None,
                "uploaded_via": "chat_image" if normalized_session_id else "manual_image_upload",
                "media_type": "image",
                "analysis_mode": analysis_result.mode,
                "analysis_provider": analysis_result.provider,
                **analysis_result.metadata,
            },
        )
        base_response = await ingest_text(request, current_user=current_user, tenant_id=tenant_id)
        _record_media_event(
            media_type="image",
            status="accepted",
            filename=file.filename or "imagem.png",
            session_id=normalized_session_id,
            current_user=current_user,
            content_size=len(content),
        )
        payload = base_response.model_dump() if hasattr(base_response, "model_dump") else base_response.dict()
        payload["analysis_summary"] = analysis_result.summary
        return IngestResponse(**payload)
    except HTTPException:
        _record_media_event(
            media_type="image",
            status="rejected",
            filename=file.filename or "imagem.png",
            session_id=normalized_session_id,
            current_user=current_user,
            error_message="http_exception",
        )
        raise
    except Exception as e:
        logger.error("ingest_image_error", error=str(e))
        _record_media_event(
            media_type="image",
            status="rejected",
            filename=file.filename or "imagem.png",
            session_id=normalized_session_id,
            current_user=current_user,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))
