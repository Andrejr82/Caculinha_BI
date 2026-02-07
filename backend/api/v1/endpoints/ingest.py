"""
Ingest Endpoint — API de Ingestão de Documentos

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
import structlog

from backend.domain.entities.document import Document

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["Ingest"])


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


# Placeholder para adapters (injetados via dependency)
_vector_adapter = None
_vectorization_agent = None


def set_ingest_dependencies(vector_adapter, vectorization_agent):
    """Configura dependências (chamado no startup)."""
    global _vector_adapter, _vectorization_agent
    _vector_adapter = vector_adapter
    _vectorization_agent = vectorization_agent


@router.post("", response_model=IngestResponse)
async def ingest_text(
    request: IngestRequest,
    tenant_id: str = "default",
):
    """
    Ingere texto como documento para RAG.
    
    Pipeline:
    1. Divide em chunks
    2. Gera embeddings
    3. Indexa no vector store
    """
    logger.info("ingest_request", content_len=len(request.content), tenant_id=tenant_id)
    
    try:
        # Cria chunks do documento
        chunks = Document.create_chunks(
            tenant_id=tenant_id,
            content=request.content,
            chunk_size=512,
            source=request.source,
            metadata=request.metadata,
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
        
        logger.info("ingest_complete", chunks=len(chunks), tenant_id=tenant_id)
        
        return IngestResponse(
            document_ids=document_ids,
            chunks_count=len(chunks),
            success=True,
        )
    
    except Exception as e:
        logger.error("ingest_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    tenant_id: str = Form("default"),
):
    """Ingere arquivo (TXT, CSV, etc)."""
    logger.info("ingest_file", filename=file.filename, tenant_id=tenant_id)
    
    try:
        content = await file.read()
        text = content.decode("utf-8")
        
        request = IngestRequest(content=text, source=file.filename or "upload")
        return await ingest_text(request, tenant_id=tenant_id)
    
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Arquivo deve ser texto UTF-8")
    except Exception as e:
        logger.error("ingest_file_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
