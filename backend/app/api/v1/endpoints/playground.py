from typing import Annotated, Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
from uuid import uuid4

import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from backend.app.api.dependencies import require_role, get_current_active_user, get_db
from backend.app.core.data_scope_service import data_scope_service
from backend.app.infrastructure.database.models import User, UserPreference, AuditLog
from backend.app.config.settings import settings
from backend.app.core.llm_gemini_adapter import GeminiLLMAdapter
from backend.app.core.llm_factory import LLMFactory
from backend.app.core.playground_rules_engine import resolve_playground_rule, load_bi_intents_catalog
from backend.app.core.playground_template_engine import resolve_playground_template, load_bi_templates_catalog
from backend.app.core.playground_output_validator import validate_playground_output
from backend.app.core.playground_sql_access import evaluate_sql_access, parse_sql_access_context
from backend.app.core.playground_mode import (
    is_remote_llm_enabled_for_user,
    is_user_in_canary,
    mode_label,
)
from backend.app.core.playground_response_schema import enforce_playground_response_schema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/playground", tags=["Playground"])

_INTENTS_CATALOG = load_bi_intents_catalog()
_TEMPLATES_CATALOG = load_bi_templates_catalog()
PLAYGROUND_SQL_ACCESS_KEY = "playground_sql_full_access"
PLAYGROUND_CANARY_ACCESS_KEY = "playground_canary_access"
PLAYGROUND_ACCESS_KEY = "playground_access"
_SQL_ACCESS_CACHE_TTL_SECONDS = 60
_sql_access_cache: dict[str, tuple[datetime, tuple[bool, str, str | None]]] = {}
_canary_access_cache: dict[str, tuple[datetime, tuple[bool | None, str]]] = {}
_playground_access_cache: dict[str, tuple[datetime, tuple[bool, str]]] = {}


def _audit_playground_event(
    *,
    request_id: str,
    user: str,
    source: str,
    intent: str,
    confidence: float,
    is_safe: bool,
    reason: str
) -> None:
    logger.info(
        "playground_audit request_id=%s user=%s source=%s intent=%s confidence=%.2f is_safe=%s reason=%s",
        request_id,
        user,
        source,
        intent,
        confidence,
        is_safe,
        reason,
    )


def _safe_response_or_block(text: str) -> tuple[str, bool, str]:
    validation = validate_playground_output(text)
    if validation.is_safe:
        return text, True, validation.reason
    blocked = (
        "Conteúdo bloqueado por política de segurança do Playground. "
        "Ajuste a solicitação para uma versão somente leitura/não destrutiva."
    )
    return blocked, False, validation.reason


async def _get_sql_access_state(user: User, db: AsyncSession) -> tuple[bool, str, str | None]:
    if user.role == "admin":
        return True, "Admin com acesso total.", None
    user_key = str(user.id)
    now = datetime.utcnow()
    cached = _sql_access_cache.get(user_key)
    if cached and cached[0] > now:
        return cached[1]
    try:
        result = await db.execute(
            select(UserPreference).where(
                (UserPreference.user_id == user.id)
                & (UserPreference.key == PLAYGROUND_SQL_ACCESS_KEY)
            )
        )
    except SQLAlchemyError as e:
        logger.warning("playground_sql_access_lookup_failed: %s", e)
        state = (False, "Permissão não concedida (fallback por indisponibilidade de tabela).", None)
        _sql_access_cache[user_key] = (now + timedelta(seconds=_SQL_ACCESS_CACHE_TTL_SECONDS), state)
        return state
    pref = result.scalar_one_or_none()
    if pref is None:
        state = (False, "Permissão não concedida.", None)
        _sql_access_cache[user_key] = (now + timedelta(seconds=_SQL_ACCESS_CACHE_TTL_SECONDS), state)
        return state
    active, reason = evaluate_sql_access(str(pref.value), pref.context)
    expires_at = parse_sql_access_context(pref.context).get("expires_at")
    state = (active, reason, expires_at)
    _sql_access_cache[user_key] = (now + timedelta(seconds=_SQL_ACCESS_CACHE_TTL_SECONDS), state)
    return state


async def _get_canary_override_state(user: User, db: AsyncSession) -> tuple[bool | None, str]:
    user_key = str(user.id)
    now = datetime.utcnow()
    cached = _canary_access_cache.get(user_key)
    if cached and cached[0] > now:
        return cached[1]

    try:
        result = await db.execute(
            select(UserPreference).where(
                (UserPreference.user_id == user.id)
                & (UserPreference.key == PLAYGROUND_CANARY_ACCESS_KEY)
            )
        )
    except SQLAlchemyError as e:
        logger.warning("playground_canary_access_lookup_failed: %s", e)
        state = (None, "Sem override individual (fallback por indisponibilidade de tabela).")
        _canary_access_cache[user_key] = (now + timedelta(seconds=_SQL_ACCESS_CACHE_TTL_SECONDS), state)
        return state
    pref = result.scalar_one_or_none()
    if pref is None:
        state = (None, "Sem override individual de canário.")
        _canary_access_cache[user_key] = (now + timedelta(seconds=_SQL_ACCESS_CACHE_TTL_SECONDS), state)
        return state

    normalized = str(pref.value).strip().lower()
    if normalized not in {"true", "false"}:
        state = (None, "Override inválido; fallback para regra por grupo.")
    else:
        state = (normalized == "true", "Override individual aplicado.")
    _canary_access_cache[user_key] = (now + timedelta(seconds=_SQL_ACCESS_CACHE_TTL_SECONDS), state)
    return state


async def _get_playground_access_state(user: User, db: AsyncSession) -> tuple[bool, str]:
    if user.role == "admin":
        return True, "Admin com acesso total."
    user_key = str(user.id)
    now = datetime.utcnow()
    cached = _playground_access_cache.get(user_key)
    if cached and cached[0] > now:
        return cached[1]
    try:
        result = await db.execute(
            select(UserPreference).where(
                (UserPreference.user_id == user.id)
                & (UserPreference.key == PLAYGROUND_ACCESS_KEY)
            )
        )
    except SQLAlchemyError as e:
        logger.warning("playground_access_lookup_failed: %s", e)
        state = (False, "Acesso não configurado (fallback por indisponibilidade de tabela).")
        _playground_access_cache[user_key] = (now + timedelta(seconds=_SQL_ACCESS_CACHE_TTL_SECONDS), state)
        return state

    pref = result.scalar_one_or_none()
    enabled = bool(pref and str(pref.value).strip().lower() == "true")
    state = (enabled, "Acesso habilitado pelo administrador." if enabled else "Acesso ao Playground não habilitado para este usuário.")
    _playground_access_cache[user_key] = (now + timedelta(seconds=_SQL_ACCESS_CACHE_TTL_SECONDS), state)
    return state


async def _resolve_remote_llm_access(user: User, db: AsyncSession) -> tuple[bool, str]:
    override_value, override_reason = await _get_canary_override_state(user, db)
    in_canary = is_user_in_canary(
        user_id=str(user.id),
        username=user.username,
        role=user.role,
        canary_enabled=settings.PLAYGROUND_CANARY_ENABLED,
        allowed_roles_csv=settings.PLAYGROUND_CANARY_ALLOWED_ROLES,
        allowed_users_csv=settings.PLAYGROUND_CANARY_ALLOWED_USERS,
        user_override=override_value,
    )
    remote_enabled = is_remote_llm_enabled_for_user(
        playground_mode=settings.PLAYGROUND_MODE,
        has_gemini_key=_has_remote_llm_key(),
        canary_enabled=settings.PLAYGROUND_CANARY_ENABLED,
        user_in_canary=in_canary,
    )
    reason = (
        f"{override_reason} | canary_enabled={settings.PLAYGROUND_CANARY_ENABLED} "
        f"| user_in_canary={in_canary}"
    )
    return remote_enabled, reason


def _apply_sql_scope(
    *,
    text: str,
    has_sql_access: bool,
) -> tuple[str, bool, str]:
    validation = validate_playground_output(text)
    if validation.detected_language == "sql" and not has_sql_access:
        return (
            "SQL completo bloqueado para seu usuário. Solicite ao administrador a habilitação na Área Administrativa.",
            False,
            "SQL completo requer permissão explícita do admin.",
        )
    return text, True, "Escopo de SQL validado para o perfil."


def _build_local_fallback_response(message: str, json_mode: bool = False) -> str:
    """
    Gera resposta local quando GEMINI_API_KEY não está configurada.
    Evita UX de erro no Playground e mantém utilidade básica para prompts técnicos.
    """
    text = (message or "").lower()
    rule_result = resolve_playground_rule(message=message, json_mode=json_mode)
    if rule_result:
        return enforce_playground_response_schema(rule_result.response, json_mode=json_mode)
    template_result = resolve_playground_template(message=message, json_mode=json_mode)
    if template_result:
        return enforce_playground_response_schema(template_result.response, json_mode=json_mode)
    if "parquet" in text and "status" in text and "error" in text:
        code = (
            "import polars as pl\n\n"
            "df = pl.read_parquet('dados.parquet')\n"
            "resultado = df.filter(pl.col('status') == 'error')\n"
            "print(resultado)\n"
        )
        if json_mode:
            return json.dumps({"language": "python", "code": code}, ensure_ascii=False, indent=2)
        return (
            "Script sugerido:\n\n"
            "```python\n"
            f"{code}"
            "```"
        )

    default_msg = (
        "Playground executando em modo local (sem LLM remoto). "
        "As respostas estão em modo econômico e determinístico."
    )
    if json_mode:
        return enforce_playground_response_schema(json.dumps({"summary": default_msg, "table": {"headers": [], "rows": []}, "action": "Defina o próximo passo operacional."}, ensure_ascii=False), json_mode=True)
    return enforce_playground_response_schema(default_msg, json_mode=False)


def _has_remote_llm_key() -> bool:
    provider = (settings.LLM_PROVIDER or "").strip().lower()
    if provider == "groq":
        return bool(settings.GROQ_API_KEY)
    if provider == "google":
        return bool(settings.GEMINI_API_KEY)
    return bool(settings.GROQ_API_KEY or settings.GEMINI_API_KEY)


def _is_explicit_sql_request(message: str) -> bool:
    text = (message or "").strip().lower()
    if not text:
        return False
    sql_markers = ["sql", "query", "consulta sql", "select ", "cte ", "with "]
    return any(marker in text for marker in sql_markers)

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


class PlaygroundFeedbackRequest(BaseModel):
    request_id: str
    useful: bool
    comment: Optional[str] = None


class PlaygroundOpsApprovalRequest(BaseModel):
    operation_mode: str = Field(min_length=2, max_length=120)
    output_type: str = Field(min_length=2, max_length=40)
    request_text: str = Field(min_length=3, max_length=8000)
    generated_output: Optional[str] = Field(default=None, max_length=20000)
    parameters: Dict[str, Any] = Field(default_factory=dict)


def _record_playground_usage(
    db: AsyncSession,
    *,
    user_id,
    action: str,
    details: dict,
    status: str = "success",
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource="playground_usage",
            details=details,
            ip_address="playground",
            status=status,
        )
    )


async def _safe_db_commit(db: AsyncSession, context: str) -> None:
    """Best-effort commit: do not break Playground flow if audit tables are missing."""
    try:
        await db.commit()
    except SQLAlchemyError as e:
        logger.warning("playground_db_commit_failed context=%s error=%s", context, e)
        try:
            await db.rollback()
        except SQLAlchemyError:
            pass


def _extract_endpoint_from_action(action: str) -> str:
    normalized = (action or "").lower()
    if "_chat_" in normalized:
        return "chat"
    if "_stream_" in normalized:
        return "stream"
    return "unknown"


def _to_number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    idx = int(round((pct / 100.0) * (len(sorted_values) - 1)))
    idx = min(max(idx, 0), len(sorted_values) - 1)
    return round(sorted_values[idx], 2)

@router.post("/stream")
async def playground_stream(
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: PlaygroundChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Streaming endpoint for Playground.
    Supports streaming response via SSE (Server-Sent Events).
    """
    from fastapi.responses import StreamingResponse
    request_id = str(uuid4())
    has_playground_access, playground_access_reason = await _get_playground_access_state(current_user, db)
    if not has_playground_access:
        raise HTTPException(status_code=403, detail=playground_access_reason)
    has_sql_access, sql_access_reason, _ = await _get_sql_access_state(current_user, db)
    remote_llm_allowed, remote_llm_reason = await _resolve_remote_llm_access(current_user, db)

    is_sql_request = _is_explicit_sql_request(request.message)

    rule_result = resolve_playground_rule(message=request.message, json_mode=request.json_mode) if not is_sql_request else None
    if rule_result:
        normalized = enforce_playground_response_schema(rule_result.response, json_mode=request.json_mode)
        scoped_text, scope_ok, scope_reason = _apply_sql_scope(
            text=normalized,
            has_sql_access=has_sql_access,
        )
        safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
        _audit_playground_event(
            request_id=request_id,
            user=current_user.username,
            source=rule_result.source,
            intent=rule_result.intent,
            confidence=rule_result.confidence,
            is_safe=is_safe and scope_ok,
            reason=f"{sql_access_reason} | {scope_reason} | {safety_reason}",
        )
        _record_playground_usage(
            db,
            user_id=current_user.id,
            action="playground_stream_rule",
            details={"request_id": request_id, "intent": rule_result.intent, "source": rule_result.source, "endpoint": "stream", "duration_ms": 0},
        )
        await _safe_db_commit(db, "playground")
        async def rule_generator():
            start_time = datetime.now()
            yield f"data: {json.dumps({'type': 'start', 'request_id': request_id, 'model': rule_result.source, 'intent': rule_result.intent, 'confidence': rule_result.confidence})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'text': safe_text})}\n\n"
            duration = (datetime.now() - start_time).total_seconds()
            yield f"data: {json.dumps({'type': 'done', 'request_id': request_id, 'metrics': {'time': duration, 'tokens': max(1, len(safe_text)//4)}, 'safety': {'is_safe': is_safe, 'reason': safety_reason}})}\n\n"
        return StreamingResponse(rule_generator(), media_type="text/event-stream")
    template_result = resolve_playground_template(message=request.message, json_mode=request.json_mode) if not is_sql_request else None
    if template_result:
        normalized = enforce_playground_response_schema(template_result.response, json_mode=request.json_mode)
        scoped_text, scope_ok, scope_reason = _apply_sql_scope(
            text=normalized,
            has_sql_access=has_sql_access,
        )
        safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
        _audit_playground_event(
            request_id=request_id,
            user=current_user.username,
            source=template_result.source,
            intent=template_result.intent,
            confidence=template_result.confidence,
            is_safe=is_safe and scope_ok,
            reason=f"{sql_access_reason} | {scope_reason} | {safety_reason}",
        )
        _record_playground_usage(
            db,
            user_id=current_user.id,
            action="playground_stream_template",
            details={"request_id": request_id, "intent": template_result.intent, "source": template_result.source, "endpoint": "stream", "duration_ms": 0},
        )
        await _safe_db_commit(db, "playground")
        async def template_generator():
            start_time = datetime.now()
            yield f"data: {json.dumps({'type': 'start', 'request_id': request_id, 'model': template_result.source, 'intent': template_result.intent, 'confidence': template_result.confidence, 'route_layer': 'template'})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'text': safe_text})}\n\n"
            duration = (datetime.now() - start_time).total_seconds()
            yield f"data: {json.dumps({'type': 'done', 'request_id': request_id, 'metrics': {'time': duration, 'tokens': max(1, len(safe_text)//4)}, 'safety': {'is_safe': is_safe, 'reason': safety_reason}})}\n\n"
        return StreamingResponse(template_generator(), media_type="text/event-stream")

    if not _has_remote_llm_key():
        async def fallback_generator():
            start_time = datetime.now()
            fallback_text = _build_local_fallback_response(
                message=request.message,
                json_mode=request.json_mode,
            )
            normalized = enforce_playground_response_schema(fallback_text, json_mode=request.json_mode)
            scoped_text, scope_ok, scope_reason = _apply_sql_scope(
                text=normalized,
                has_sql_access=has_sql_access,
            )
            safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
            _audit_playground_event(
                request_id=request_id,
                user=current_user.username,
                source="local-fallback",
                intent="fallback.default",
                confidence=0.7,
                is_safe=is_safe and scope_ok,
                reason=f"{sql_access_reason} | {scope_reason} | {safety_reason}",
            )
            _record_playground_usage(
                db,
                user_id=current_user.id,
                action="playground_stream_fallback",
                details={"request_id": request_id, "intent": "fallback.default", "source": "local-fallback", "endpoint": "stream", "duration_ms": 0},
            )
            await _safe_db_commit(db, "playground")
            yield f"data: {json.dumps({'type': 'start', 'request_id': request_id, 'model': 'local-fallback'})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'text': safe_text})}\n\n"
            duration = (datetime.now() - start_time).total_seconds()
            yield f"data: {json.dumps({'type': 'done', 'request_id': request_id, 'metrics': {'time': duration, 'tokens': max(1, len(safe_text)//4)}, 'safety': {'is_safe': is_safe, 'reason': safety_reason}})}\n\n"
        return StreamingResponse(fallback_generator(), media_type="text/event-stream")
    if not remote_llm_allowed:
        async def local_mode_generator():
            start_time = datetime.now()
            fallback_text = _build_local_fallback_response(
                message=request.message,
                json_mode=request.json_mode,
            )
            normalized = enforce_playground_response_schema(fallback_text, json_mode=request.json_mode)
            scoped_text, _, _ = _apply_sql_scope(text=normalized, has_sql_access=has_sql_access)
            safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
            yield f"data: {json.dumps({'type': 'start', 'request_id': request_id, 'model': 'local-only', 'reason': remote_llm_reason})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'text': safe_text})}\n\n"
            duration = (datetime.now() - start_time).total_seconds()
            yield f"data: {json.dumps({'type': 'done', 'request_id': request_id, 'metrics': {'time': duration, 'tokens': max(1, len(safe_text)//4)}, 'safety': {'is_safe': is_safe, 'reason': safety_reason}})}\n\n"
        return StreamingResponse(local_mode_generator(), media_type="text/event-stream")

    provider = (settings.LLM_PROVIDER or "").strip().lower()
    model_name = settings.GROQ_MODEL_NAME if provider == "groq" else settings.LLM_MODEL_NAME

    # Prepare messages
    messages = []
    for msg in request.history:
        role = "model" if msg.role == "assistant" else "user"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    async def event_generator():
        llm_adapter = None
        try:
            # Groq path via unified factory; Gemini keeps legacy adapter path.
            if provider == "groq":
                llm_adapter = LLMFactory.get_adapter(provider="groq", use_smart=True)
                if hasattr(llm_adapter, "system_instruction"):
                    llm_adapter.system_instruction = request.system_instruction
            else:
                llm_adapter = GeminiLLMAdapter(
                    model_name=model_name,
                    gemini_api_key=settings.GEMINI_API_KEY,
                    system_instruction=request.system_instruction
                )

            # Yield start event
            yield f"data: {json.dumps({'type': 'start', 'request_id': request_id, 'model': model_name})}\n\n"
            
            # Since stream_completion is a sync generator (using yield), we iterate it
            # But we are in an async function. 
            # Ideally GeminiLLMAdapter.stream_completion should be async or we run it in thread.
            # But the underlying google genai stream is sync iterator usually.
            # Let's assume direct iteration works for now or wrap it if it blocks.
            
            start_time = datetime.now()
            
            # Use asyncio.to_thread for blocking generator if needed, 
            # but you can't easily iterate a sync generator in a thread from async loop without wrappers.
            # For simplicity, we'll iterate directly (might block loop slightly but ok for playground)
            
            full_text = ""
            if provider == "groq":
                result = llm_adapter.get_completion(messages)
                if "error" in result:
                    lower = str(result["error"]).lower()
                    if any(key in lower for key in ["429", "quota", "rate", "resource_exhausted"]):
                        yield f"data: {json.dumps({'type': 'degraded', 'text': 'Quota estourada / configure billing / tente depois'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'text': 'Falha temporaria no Playground. Tente novamente em instantes.'})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'request_id': request_id})}\n\n"
                    return
                full_text = str(result.get("content", "") or "")
                if full_text:
                    yield f"data: {json.dumps({'type': 'token', 'text': full_text})}\n\n"
            else:
                iterator = llm_adapter.stream_completion(messages)
                for chunk in iterator:
                    if "content" in chunk:
                        text = chunk["content"]
                        full_text += text
                        yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"
                    elif "error" in chunk:
                        lower = str(chunk["error"]).lower()
                        if any(key in lower for key in ["429", "quota", "rate", "resource_exhausted"]):
                            yield f"data: {json.dumps({'type': 'degraded', 'text': 'Quota estourada / configure billing / tente depois'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'error', 'text': 'Falha temporaria no Playground. Tente novamente em instantes.'})}\n\n"
            
            duration = (datetime.now() - start_time).total_seconds()
            scoped_text, scope_ok, scope_reason = _apply_sql_scope(
                text=full_text,
                has_sql_access=has_sql_access,
            )
            safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
            _audit_playground_event(
                request_id=request_id,
                user=current_user.username,
                source=model_name,
                intent="llm.freeform",
                confidence=0.75,
                is_safe=is_safe and scope_ok,
                reason=f"{sql_access_reason} | {scope_reason} | {safety_reason}",
            )
            _record_playground_usage(
                db,
                user_id=current_user.id,
                action="playground_stream_remote",
                details={"request_id": request_id, "intent": "llm.freeform", "source": model_name, "endpoint": "stream", "duration_ms": round(duration * 1000, 2)},
            )
            await _safe_db_commit(db, "playground")
            if not is_safe:
                yield f"data: {json.dumps({'type': 'warning', 'text': safe_text})}\n\n"
            
            # Yield done event with stats
            yield f"data: {json.dumps({'type': 'done', 'request_id': request_id, 'metrics': {'time': duration, 'tokens': len(full_text)//4}, 'safety': {'is_safe': is_safe, 'reason': safety_reason}})}\n\n"
            
        except Exception as e:
            logger.error(f"Playground stream error request_id={request_id}: {e}")
            _record_playground_usage(
                db,
                user_id=current_user.id,
                action="playground_stream_remote_error",
                details={"request_id": request_id, "endpoint": "stream", "error": str(e)},
                status="error",
            )
            await _safe_db_commit(db, "playground")
            lower = str(e).lower()
            if any(key in lower for key in ["429", "quota", "rate", "resource_exhausted"]):
                yield f"data: {json.dumps({'type': 'degraded', 'text': 'Quota estourada / configure billing / tente depois'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'text': 'Falha temporaria no Playground. Tente novamente em instantes.'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'request_id': request_id})}\n\n"

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
        raise HTTPException(status_code=500, detail="Falha ao executar consulta no Playground.")


@router.post("/chat")
async def playground_chat(
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: PlaygroundChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Endpoint de chat do Playground com controles avançados.
    Permite testar o modelo Gemini com diferentes parâmetros.
    """
    try:
        request_id = str(uuid4())
        has_playground_access, playground_access_reason = await _get_playground_access_state(current_user, db)
        if not has_playground_access:
            raise HTTPException(status_code=403, detail=playground_access_reason)
        has_sql_access, sql_access_reason, sql_access_expires_at = await _get_sql_access_state(current_user, db)
        remote_llm_allowed, remote_llm_reason = await _resolve_remote_llm_access(current_user, db)
        # Validar mensagem não vazia
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="A mensagem não pode estar vazia. Por favor, digite algo."
            )

        is_sql_request = _is_explicit_sql_request(request.message)

        rule_result = resolve_playground_rule(message=request.message, json_mode=request.json_mode) if not is_sql_request else None
        if rule_result:
            normalized = enforce_playground_response_schema(rule_result.response, json_mode=request.json_mode)
            scoped_text, scope_ok, scope_reason = _apply_sql_scope(
                text=normalized,
                has_sql_access=has_sql_access,
            )
            safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
            _audit_playground_event(
                request_id=request_id,
                user=current_user.username,
                source=rule_result.source,
                intent=rule_result.intent,
                confidence=rule_result.confidence,
                is_safe=is_safe and scope_ok,
                reason=f"{sql_access_reason} | {scope_reason} | {safety_reason}",
            )
            _record_playground_usage(
                db,
                user_id=current_user.id,
                action="playground_chat_rule",
                details={"request_id": request_id, "intent": rule_result.intent, "source": rule_result.source, "endpoint": "chat", "duration_ms": 0},
            )
            await _safe_db_commit(db, "playground")
            return {
                "response": safe_text,
                "model_info": {
                    "model": rule_result.source,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "json_mode": request.json_mode,
                    "confidence": rule_result.confidence,
                    "intent": rule_result.intent,
                },
                "metadata": {
                    "response_time": 0.0,
                    "timestamp": datetime.now().isoformat(),
                    "user": current_user.username,
                    "request_id": request_id,
                    "source": rule_result.source,
                    "intent": rule_result.intent,
                    "sql_access_expires_at": sql_access_expires_at,
                    "safety": {"is_safe": is_safe and scope_ok, "reason": f"{sql_access_reason} | {scope_reason} | {safety_reason}"}
                },
                "cache_stats": {
                    "hits": 0,
                    "misses": 0,
                    "hit_rate": 0.0,
                    "enabled": False
                }
            }
        template_result = resolve_playground_template(message=request.message, json_mode=request.json_mode) if not is_sql_request else None
        if template_result:
            normalized = enforce_playground_response_schema(template_result.response, json_mode=request.json_mode)
            scoped_text, scope_ok, scope_reason = _apply_sql_scope(
                text=normalized,
                has_sql_access=has_sql_access,
            )
            safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
            _audit_playground_event(
                request_id=request_id,
                user=current_user.username,
                source=template_result.source,
                intent=template_result.intent,
                confidence=template_result.confidence,
                is_safe=is_safe and scope_ok,
                reason=f"{sql_access_reason} | {scope_reason} | {safety_reason}",
            )
            _record_playground_usage(
                db,
                user_id=current_user.id,
                action="playground_chat_template",
                details={"request_id": request_id, "intent": template_result.intent, "source": template_result.source, "endpoint": "chat", "duration_ms": 0},
            )
            await _safe_db_commit(db, "playground")
            return {
                "response": safe_text,
                "model_info": {
                    "model": template_result.source,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "json_mode": request.json_mode,
                    "confidence": template_result.confidence,
                    "intent": template_result.intent,
                    "route_layer": "template",
                },
                "metadata": {
                    "response_time": 0.0,
                    "timestamp": datetime.now().isoformat(),
                    "user": current_user.username,
                    "request_id": request_id,
                    "source": template_result.source,
                    "intent": template_result.intent,
                    "sql_access_expires_at": sql_access_expires_at,
                    "safety": {"is_safe": is_safe and scope_ok, "reason": f"{sql_access_reason} | {scope_reason} | {safety_reason}"}
                },
                "cache_stats": {"hits": 0, "misses": 0, "hit_rate": 0.0, "enabled": False}
            }

        if not _has_remote_llm_key() or not remote_llm_allowed:
            fallback_text = _build_local_fallback_response(
                message=request.message,
                json_mode=request.json_mode,
            )
            normalized = enforce_playground_response_schema(fallback_text, json_mode=request.json_mode)
            scoped_text, scope_ok, scope_reason = _apply_sql_scope(
                text=normalized,
                has_sql_access=has_sql_access,
            )
            safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
            _audit_playground_event(
                request_id=request_id,
                user=current_user.username,
                source="local-fallback",
                intent="fallback.default",
                confidence=0.7,
                is_safe=is_safe and scope_ok,
                reason=f"{sql_access_reason} | {scope_reason} | {safety_reason}",
            )
            _record_playground_usage(
                db,
                user_id=current_user.id,
                action="playground_chat_fallback",
                details={"request_id": request_id, "intent": "fallback.default", "source": "local-fallback", "endpoint": "chat", "duration_ms": 0},
            )
            await _safe_db_commit(db, "playground")
            return {
                "response": safe_text,
                "model_info": {
                    "model": "local-fallback",
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "json_mode": request.json_mode
                },
                "metadata": {
                    "response_time": 0.0,
                    "timestamp": datetime.now().isoformat(),
                    "user": current_user.username,
                    "request_id": request_id,
                    "source": "local-fallback",
                    "intent": "fallback.default",
                    "remote_llm_reason": remote_llm_reason,
                    "sql_access_expires_at": sql_access_expires_at,
                    "safety": {"is_safe": is_safe and scope_ok, "reason": f"{sql_access_reason} | {scope_reason} | {safety_reason}"}
                },
                "cache_stats": {
                    "hits": 0,
                    "misses": 0,
                    "hit_rate": 0.0,
                    "enabled": False
                }
            }

        provider = (settings.LLM_PROVIDER or "").strip().lower()
        model_source = settings.GROQ_MODEL_NAME if provider == "groq" else settings.LLM_MODEL_NAME

        # Invocar LLM
        start_time = datetime.now()
        if provider == "groq":
            messages: list[dict[str, str]] = []
            for msg in request.history:
                role = "model" if msg.role == "assistant" else "user"
                messages.append({"role": role, "content": msg.content})
            messages.append({"role": "user", "content": request.message})

            llm_adapter = LLMFactory.get_adapter(provider="groq", use_smart=True)
            if hasattr(llm_adapter, "system_instruction"):
                llm_adapter.system_instruction = request.system_instruction
            result = llm_adapter.get_completion(messages)
            if "error" in result:
                raise Exception(str(result["error"]))
            response_text = str(result.get("content", "") or "")
        else:
            llm = GeminiLLMAdapter(
                model_name=settings.LLM_MODEL_NAME,
                gemini_api_key=settings.GEMINI_API_KEY,
                system_instruction=request.system_instruction
            ).get_llm()
            messages = []
            for msg in request.history:
                if msg.role == "user":
                    messages.append(("human", msg.content))
                elif msg.role == "assistant":
                    messages.append(("assistant", msg.content))
            messages.append(("human", request.message))
            response = llm.invoke(messages)
            response_text = str(response.content or "")

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        scoped_text, scope_ok, scope_reason = _apply_sql_scope(
            text=response_text,
            has_sql_access=has_sql_access,
        )
        safe_text, is_safe, safety_reason = _safe_response_or_block(scoped_text)
        _audit_playground_event(
            request_id=request_id,
            user=current_user.username,
            source=model_source,
            intent="llm.freeform",
            confidence=0.75,
            is_safe=is_safe and scope_ok,
            reason=f"{sql_access_reason} | {scope_reason} | {safety_reason}",
        )
        _record_playground_usage(
            db,
            user_id=current_user.id,
            action="playground_chat_remote",
            details={"request_id": request_id, "intent": "llm.freeform", "source": model_source, "endpoint": "chat", "duration_ms": round(response_time * 1000, 2)},
        )
        await _safe_db_commit(db, "playground")

        # Estatísticas de cache (simuladas por enquanto)
        # Em produção, você poderia usar Redis ou outro sistema de cache
        cache_stats = {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
            "enabled": False
        }

        return {
            "response": safe_text,
            "model_info": {
                "model": model_source,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "json_mode": request.json_mode
            },
            "metadata": {
                "response_time": round(response_time, 2),
                "timestamp": datetime.now().isoformat(),
                "user": current_user.username,
                "request_id": request_id,
                "source": model_source,
                "intent": "llm.freeform",
                "sql_access_expires_at": sql_access_expires_at,
                "safety": {"is_safe": is_safe and scope_ok, "reason": f"{sql_access_reason} | {scope_reason} | {safety_reason}"}
            },
            "cache_stats": cache_stats
        }

    except Exception as e:
        logger.error(f"Erro no playground chat: {e}", exc_info=True)
        try:
            _record_playground_usage(
                db,
                user_id=current_user.id,
                action="playground_chat_error",
                details={"request_id": request_id if "request_id" in locals() else None, "endpoint": "chat", "error": str(e)},
                status="error",
            )
            await _safe_db_commit(db, "playground")
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail="Nao foi possivel processar a mensagem no Playground agora."
        )


@router.get("/info")
async def get_model_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Retorna informações sobre o modelo LLM configurado.
    """
    has_playground_access, playground_access_reason = await _get_playground_access_state(current_user, db)
    has_sql_access, sql_access_reason, sql_access_expires_at = await _get_sql_access_state(current_user, db)
    remote_llm_enabled_for_user, remote_llm_reason = await _resolve_remote_llm_access(current_user, db)
    canary_override, canary_override_reason = await _get_canary_override_state(current_user, db)
    user_in_canary = is_user_in_canary(
        user_id=str(current_user.id),
        username=current_user.username,
        role=current_user.role,
        canary_enabled=settings.PLAYGROUND_CANARY_ENABLED,
        allowed_roles_csv=settings.PLAYGROUND_CANARY_ALLOWED_ROLES,
        allowed_users_csv=settings.PLAYGROUND_CANARY_ALLOWED_USERS,
        user_override=canary_override,
    )
    return {
        "model": settings.GROQ_MODEL_NAME if (settings.LLM_PROVIDER or "").strip().lower() == "groq" else settings.LLM_MODEL_NAME,
        "api_key_configured": _has_remote_llm_key(),
        "playground_mode": settings.PLAYGROUND_MODE,
        "playground_mode_label": mode_label(settings.PLAYGROUND_MODE),
        "remote_llm_enabled": remote_llm_enabled_for_user,
        "remote_llm_reason": remote_llm_reason,
        "playground_canary_enabled": settings.PLAYGROUND_CANARY_ENABLED,
        "playground_canary_allowed_roles": settings.PLAYGROUND_CANARY_ALLOWED_ROLES,
        "playground_canary_allowed_users": settings.PLAYGROUND_CANARY_ALLOWED_USERS,
        "playground_canary_user_in_scope": user_in_canary,
        "playground_canary_user_override": canary_override,
        "playground_canary_user_override_reason": canary_override_reason,
        "routing_mode": "rules-first",
        "router_layers": ["rule", "template", "local_fallback", "remote_optional"],
        "sql_full_access_enabled": has_sql_access,
        "sql_full_access_reason": sql_access_reason,
        "sql_full_access_expires_at": sql_access_expires_at,
        "playground_access_enabled": has_playground_access,
        "playground_access_reason": playground_access_reason,
        "intents_catalog_version": _INTENTS_CATALOG.get("version", "unknown"),
        "intents_catalog_count": len(_INTENTS_CATALOG.get("intents", [])),
        "templates_catalog_version": _TEMPLATES_CATALOG.get("version", "unknown"),
        "templates_catalog_count": len(_TEMPLATES_CATALOG.get("templates", [])),
        "default_temperature": 1.0,
        "default_max_tokens": 2048,
        "max_temperature": 2.0,
        "max_tokens_limit": 8192
    }


@router.post("/feedback")
async def submit_playground_feedback(
    payload: PlaygroundFeedbackRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    has_playground_access, playground_access_reason = await _get_playground_access_state(current_user, db)
    if not has_playground_access:
        raise HTTPException(status_code=403, detail=playground_access_reason)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="playground_feedback",
            resource="playground_feedback",
            details={
                "request_id": payload.request_id,
                "useful": payload.useful,
                "comment": payload.comment,
            },
            ip_address="playground",
            status="success",
        )
    )
    await _safe_db_commit(db, "playground")
    return {"status": "ok"}


@router.post("/ops/approval")
async def submit_playground_ops_approval(
    payload: PlaygroundOpsApprovalRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    has_playground_access, playground_access_reason = await _get_playground_access_state(current_user, db)
    if not has_playground_access:
        raise HTTPException(status_code=403, detail=playground_access_reason)

    approval_id = str(uuid4())
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="playground_ops_approval_requested",
            resource="playground_ops_approval",
            details={
                "approval_id": approval_id,
                "operation_mode": payload.operation_mode,
                "output_type": payload.output_type,
                "request_text": payload.request_text,
                "generated_output": payload.generated_output,
                "parameters": payload.parameters,
                "approval_status": "pending",
            },
            ip_address="playground-ops",
            status="success",
        )
    )
    await _safe_db_commit(db, "playground")
    return {
        "status": "ok",
        "approval_id": approval_id,
        "message": "Solicitação enviada para aprovação.",
    }


@router.get("/ops/audit")
async def get_playground_ops_audit(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
):
    has_playground_access, playground_access_reason = await _get_playground_access_state(current_user, db)
    if not has_playground_access:
        raise HTTPException(status_code=403, detail=playground_access_reason)

    safe_limit = max(1, min(limit, 100))
    stmt = (
        select(AuditLog)
        .where(AuditLog.resource == "playground_ops_approval")
        .order_by(AuditLog.timestamp.desc())
        .limit(safe_limit)
    )
    if current_user.role != "admin":
        stmt = stmt.where(AuditLog.user_id == current_user.id)

    try:
        result = await db.execute(stmt)
        logs = result.scalars().all()
    except SQLAlchemyError as e:
        logger.warning("playground_ops_audit_unavailable: %s", e)
        logs = []

    items: list[dict[str, Any]] = []
    for log in logs:
        details = log.details or {}
        items.append(
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "action": log.action,
                "status": log.status,
                "approval_id": details.get("approval_id"),
                "operation_mode": details.get("operation_mode"),
                "output_type": details.get("output_type"),
                "approval_status": details.get("approval_status"),
            }
        )
    return {"items": items}


@router.get("/metrics")
async def get_playground_metrics(
    current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    since = datetime.utcnow() - timedelta(days=7)
    try:
        usage_result = await db.execute(
            select(AuditLog).where(
                (AuditLog.resource == "playground_usage")
                & (AuditLog.timestamp >= since)
            )
        )
        usage_logs = usage_result.scalars().all()
    except SQLAlchemyError as e:
        logger.warning("playground_metrics_usage_unavailable: %s", e)
        usage_logs = []

    try:
        feedback_result = await db.execute(
            select(AuditLog).where(
                (AuditLog.resource == "playground_feedback")
                & (AuditLog.timestamp >= since)
            )
        )
        feedback_logs = feedback_result.scalars().all()
    except SQLAlchemyError as e:
        logger.warning("playground_metrics_feedback_unavailable: %s", e)
        feedback_logs = []

    total_requests = len(usage_logs)
    local_requests = len([x for x in usage_logs if "fallback" in x.action or "rule" in x.action or "template" in x.action])
    remote_requests = len([x for x in usage_logs if "remote" in x.action])
    error_requests = len([x for x in usage_logs if (x.status or "").lower() != "success" or "error" in (x.action or "").lower()])
    feedback_total = len(feedback_logs)
    feedback_useful = len([x for x in feedback_logs if bool((x.details or {}).get("useful")) is True])
    feedback_not_useful = feedback_total - feedback_useful
    duration_ms_values: list[float] = []
    endpoint_buckets: dict[str, dict[str, int]] = {"chat": {"total": 0, "errors": 0}, "stream": {"total": 0, "errors": 0}, "unknown": {"total": 0, "errors": 0}}

    for log in usage_logs:
        details = log.details or {}
        endpoint = str(details.get("endpoint") or _extract_endpoint_from_action(log.action)).lower()
        if endpoint not in endpoint_buckets:
            endpoint = "unknown"
        endpoint_buckets[endpoint]["total"] += 1

        is_error = (log.status or "").lower() != "success" or "error" in (log.action or "").lower()
        if is_error:
            endpoint_buckets[endpoint]["errors"] += 1

        duration_value = _to_number(details.get("duration_ms"))
        if duration_value is not None and duration_value >= 0:
            duration_ms_values.append(duration_value)

    error_rate_by_endpoint = {
        endpoint: round((bucket["errors"] / bucket["total"]) * 100, 2) if bucket["total"] else 0.0
        for endpoint, bucket in endpoint_buckets.items()
    }

    return {
        "window_days": 7,
        "total_requests": total_requests,
        "local_requests": local_requests,
        "remote_requests": remote_requests,
        "error_requests": error_requests,
        "error_rate": round((error_requests / total_requests) * 100, 2) if total_requests else 0.0,
        "latency_ms_p95": _percentile(duration_ms_values, 95),
        "latency_ms_p99": _percentile(duration_ms_values, 99),
        "error_rate_by_endpoint": error_rate_by_endpoint,
        "feedback_total": feedback_total,
        "feedback_useful": feedback_useful,
        "feedback_not_useful": feedback_not_useful,
        "feedback_useful_rate": round((feedback_useful / feedback_total) * 100, 2) if feedback_total else 0.0,
    }
