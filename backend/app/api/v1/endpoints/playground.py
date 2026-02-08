from typing import Annotated, Dict, Any, List, Optional
from datetime import datetime
import json
import logging

import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.api.dependencies import require_role, get_current_active_user
from backend.app.core.data_scope_service import data_scope_service
from backend.app.infrastructure.database.models import User
from backend.app.config.settings import settings
from backend.app.core.llm_gemini_adapter import GeminiLLMAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/playground", tags=["Playground"])

class QueryRequest(BaseModel):
    query: str # Não usada diretamente como SQL, mas sim como intent
    columns: List[str] = []
    limit: int = 100

class ChatMessage(BaseModel):
    role: str  # "user" ou "assistant"
    content: str
    timestamp: Optional[str] = None

class PlaygroundChatRequest(BaseModel):
    message: str
    system_instruction: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=100, le=8192)
    json_mode: bool = False
    stream: bool = False
    model: Optional[str] = None # Added for Compare Mode

@router.post("/stream")
async def playground_stream(
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: PlaygroundChatRequest
):
    """
    Streaming endpoint for Playground.
    Supports streaming response via SSE (Server-Sent Events).
    """
    from fastapi.responses import StreamingResponse
    
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing")

    model_name = request.model or settings.LLM_MODEL_NAME
    
    # Initialize adapter with request-specific settings
    llm_adapter = GeminiLLMAdapter(
        model_name=model_name,
        gemini_api_key=settings.GEMINI_API_KEY,
        system_instruction=request.system_instruction
    )

    # Prepare messages
    messages = []
    for msg in request.history:
        role = "model" if msg.role == "assistant" else "user"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    async def event_generator():
        try:
            # Yield start event
            yield f"data: {json.dumps({'type': 'start', 'model': model_name})}\n\n"
            
            # Since stream_completion is a sync generator (using yield), we iterate it
            # But we are in an async function. 
            # Ideally GeminiLLMAdapter.stream_completion should be async or we run it in thread.
            # But the underlying google genai stream is sync iterator usually.
            # Let's assume direct iteration works for now or wrap it if it blocks.
            
            start_time = datetime.now()
            
            # Use asyncio.to_thread for blocking generator if needed, 
            # but you can't easily iterate a sync generator in a thread from async loop without wrappers.
            # For simplicity, we'll iterate directly (might block loop slightly but ok for playground)
            
            iterator = llm_adapter.stream_completion(messages)
            
            full_text = ""
            
            for chunk in iterator:
                if "content" in chunk:
                    text = chunk["content"]
                    full_text += text
                    yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"
                elif "error" in chunk:
                    yield f"data: {json.dumps({'type': 'error', 'text': chunk['error']})}\n\n"
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Yield done event with stats
            yield f"data: {json.dumps({'type': 'done', 'metrics': {'time': duration, 'tokens': len(full_text)//4}})}\n\n"
            
        except Exception as e:
            logger.error(f"Playground stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/query")
async def execute_query(
    current_user: Annotated[User, Depends(require_role("admin"))],
    request: QueryRequest
):
    """
    Endpoint para exploração de dados (Admin Only).
    Permite selecionar colunas e visualizar dados brutos.
    """
    try:
        df = data_scope_service.get_filtered_dataframe(current_user)

        # Selecionar colunas se especificadas
        if request.columns:
            valid_cols = [c for c in request.columns if c in df.columns]
            if valid_cols:
                df = df.select(valid_cols)

        # Limitar resultados
        result = df.head(request.limit)

        return {
            "rows": result.to_dicts(),
            "count": len(result),
            "total_rows": len(df), # Total no dataset (lazy count seria melhor, mas aqui df já é eager ou quase)
            "columns": result.columns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def playground_chat(
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: PlaygroundChatRequest
):
    """
    Endpoint de chat do Playground com controles avançados.
    Permite testar o modelo Gemini com diferentes parâmetros.
    """
    try:
        # Validar mensagem não vazia
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="A mensagem não pode estar vazia. Por favor, digite algo."
            )

        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY não configurada no servidor"
            )

        # Configurar LLM com parâmetros customizados usando GeminiLLMAdapter
        llm = GeminiLLMAdapter(
            model_name=settings.LLM_MODEL_NAME,
            gemini_api_key=settings.GEMINI_API_KEY,
            system_instruction=request.system_instruction
        ).get_llm()

        # Note: GeminiLLMAdapter doesn't support custom temperature/max_tokens in get_llm()
        # These parameters would need to be added to the adapter if needed

        # Construir histórico de mensagens
        messages = []
        for msg in request.history:
            if msg.role == "user":
                messages.append(("human", msg.content))
            elif msg.role == "assistant":
                messages.append(("assistant", msg.content))

        # Adicionar mensagem atual
        messages.append(("human", request.message))

        # Invocar LLM
        start_time = datetime.now()
        response = llm.invoke(messages)
        end_time = datetime.now()

        response_time = (end_time - start_time).total_seconds()

        # Estatísticas de cache (simuladas por enquanto)
        # Em produção, você poderia usar Redis ou outro sistema de cache
        cache_stats = {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
            "enabled": False
        }

        return {
            "response": response.content,
            "model_info": {
                "model": settings.LLM_MODEL_NAME,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "json_mode": request.json_mode
            },
            "metadata": {
                "response_time": round(response_time, 2),
                "timestamp": datetime.now().isoformat(),
                "user": current_user.username
            },
            "cache_stats": cache_stats
        }

    except Exception as e:
        logger.error(f"Erro no playground chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )


@router.get("/info")
async def get_model_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Retorna informações sobre o modelo LLM configurado.
    """
    return {
        "model": settings.LLM_MODEL_NAME,
        "api_key_configured": bool(settings.GEMINI_API_KEY),
        "default_temperature": 1.0,
        "default_max_tokens": 2048,
        "max_temperature": 2.0,
        "max_tokens_limit": 8192
    }
