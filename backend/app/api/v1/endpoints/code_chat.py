"""
Code Chat API Endpoints
=======================

Provides REST API for semantic code search and analysis.

Endpoints:
- GET  /api/v1/code-chat/stats - Get index statistics
- POST /api/v1/code-chat/query - Query the codebase

Author: Antigravity AI
Date: 2025-12-15
"""

from typing import Annotated, List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import require_role
from app.infrastructure.database.models import User
from app.core.code_rag_service import get_code_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code-chat", tags=["Code Chat"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class CodeChatRequest(BaseModel):
    """Request model for code chat queries."""
    message: str = Field(..., min_length=1, description="User's question about the code")
    history: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
    filters: Optional[dict] = Field(default=None, description="Optional filters (language, directory)")


class CodeReference(BaseModel):
    """Code reference model."""
    file: str
    score: float
    content: str
    lines: str


class CodeChatResponse(BaseModel):
    """Response model for code chat queries."""
    response: str
    code_references: List[CodeReference]
    metadata: dict


class IndexStats(BaseModel):
    """Index statistics model."""
    status: str
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    indexed_at: Optional[str]
    languages: List[str]


# ============================================================================
# Endpoints
# ============================================================================

from fastapi.responses import StreamingResponse
import json

@router.get("/stream")
async def stream_code_chat(
    q: str,
    token: str,
    current_user: Annotated[User, Depends(require_role("admin"))] # In real SSE, auth is via token param usually, but here we can rely on dependency if client sends header? 
    # SSE clients (EventSource) don't send headers easily. We usually pass token in query param.
    # But for this existing project structure, let's look at chat.py: it uses `token` param and `get_current_user_from_token`.
):
    """
    Streaming endpoint for code chat.
    """
    from app.api.dependencies import get_current_user_from_token
    
    # Manual auth check for SSE
    try:
        user = await get_current_user_from_token(token)
        if user.role != "admin": # Enforce admin role for code chat
             raise HTTPException(status_code=403, detail="Not authorized")
    except Exception as e:
        logger.error(f"SSE Auth failed: {e}")
        # Return strict error event
        async def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'content': 'Authentication failed'})}\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    rag_service = get_code_rag_service()
    
    async def event_generator():
        try:
            # Fake history for now or pass via query param JSON (complex)
            # For this iteration, we start fresh or implement history param later
            history = [] 
            
            # Initial progress event
            yield f"data: {json.dumps({'type': 'progress', 'step': 'searching', 'message': 'Searching codebase...'})}\n\n"
            
            # Stream from service
            # Note: stream_query is a generator, we need to iterate it
            # If stream_query is sync (yielding), we wrap it. If async, await.
            # LlamaIndex stream is usually sync generator.
            
            iterator = rag_service.stream_query(message=q, history=history)
            
            for chunk in iterator:
                # If references found, notify UI
                if chunk['type'] == 'references':
                    yield f"data: {json.dumps({'type': 'progress', 'step': 'analyzing', 'message': 'Analyzing code...'})}\n\n"
                    yield f"data: {json.dumps(chunk)}\n\n"
                    yield f"data: {json.dumps({'type': 'progress', 'step': 'streaming', 'message': 'Generating response...'})}\n\n"
                else:
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/stats", response_model=IndexStats)
async def get_index_stats(
    current_user: Annotated[User, Depends(require_role("admin"))]
):
    """
    Get statistics about the code index.
    
    Returns:
        IndexStats: Statistics about indexed code
    """
    try:
        rag_service = get_code_rag_service()
        stats = rag_service.get_index_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting index stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter estatísticas do índice: {str(e)}"
        )


@router.post("/query", response_model=CodeChatResponse)
async def query_codebase(
    request: CodeChatRequest,
    current_user: Annotated[User, Depends(require_role("admin"))]
):
    """
    Query the codebase with semantic search.
    
    Args:
        request: CodeChatRequest with message, history, and filters
        current_user: Authenticated user
        
    Returns:
        CodeChatResponse: Response with code references and metadata
    """
    try:
        # Validate message
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="A mensagem não pode estar vazia"
            )
        
        # Get RAG service
        rag_service = get_code_rag_service()
        
        # Convert history to dict format
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in request.history
        ]
        
        # Query the codebase
        logger.info(f"Code chat query from {current_user.username}: {request.message[:100]}...")
        result = rag_service.query(
            message=request.message,
            history=history_dicts,
            filters=request.filters
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in code chat query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar consulta: {str(e)}"
        )
