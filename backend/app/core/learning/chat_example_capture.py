import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


_DEGRADED_RESPONSE_MARKERS = (
    "não consegui gerar o gráfico",
    "nao consegui gerar o grafico",
    "não encontrei dados",
    "nao encontrei dados",
    "desculpe, não consegui gerar uma resposta adequada",
    "desculpe, nao consegui gerar uma resposta adequada",
    "aguarde alguns segundos e tente novamente",
    "recursos multimodais não estão habilitados",
    "recursos multimodais nao estao habilitados",
)
_BLOCKED_MODE_PREFIXES = ("policy", "error", "timeout", "rate_limit", "clarification")
_BLOCKED_SOURCE_PREFIXES = ("policy.", "automation.")
_ALLOWED_RESPONSE_TYPES = {"text", "chart", "dashboard", "table"}
_CODE_BLOCK_PATTERN = re.compile(r"```(?:[\w+-]+)?\n(.*?)```", re.DOTALL)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def _extract_response_text(response: Optional[Dict[str, Any]], assistant_text: Optional[str]) -> str:
    if assistant_text not in (None, ""):
        return _clean_text(assistant_text)
    if not isinstance(response, dict):
        return ""
    if isinstance(response.get("result"), dict) and isinstance(response["result"].get("mensagem"), str):
        return _clean_text(response["result"]["mensagem"])
    if isinstance(response.get("response_text"), str):
        return _clean_text(response["response_text"])
    if isinstance(response.get("response"), str):
        return _clean_text(response["response"])
    if isinstance(response.get("result"), str):
        return _clean_text(response["result"])
    return ""


def extract_code_blocks(text: str) -> str:
    matches = [_clean_text(match) for match in _CODE_BLOCK_PATTERN.findall(text or "")]
    return "\n\n".join(match for match in matches if match)


def _extract_source(response: Optional[Dict[str, Any]], assistant_metadata: Dict[str, Any]) -> str:
    response = response if isinstance(response, dict) else {}
    internal_meta = response.get("_internal_meta") if isinstance(response.get("_internal_meta"), dict) else {}
    context = assistant_metadata.get("context") if isinstance(assistant_metadata.get("context"), dict) else {}
    for candidate in (
        response.get("source"),
        internal_meta.get("source"),
        assistant_metadata.get("source"),
        context.get("source"),
    ):
        normalized = _clean_text(candidate)
        if normalized:
            return normalized
    return ""


def _extract_mode(response: Optional[Dict[str, Any]], assistant_metadata: Dict[str, Any]) -> str:
    response = response if isinstance(response, dict) else {}
    internal_meta = response.get("_internal_meta") if isinstance(response.get("_internal_meta"), dict) else {}
    for candidate in (
        response.get("mode"),
        internal_meta.get("mode"),
        assistant_metadata.get("mode"),
    ):
        normalized = _clean_text(candidate)
        if normalized:
            return normalized
    return ""


def _extract_confidence(response: Optional[Dict[str, Any]], assistant_metadata: Dict[str, Any]) -> Optional[float]:
    response = response if isinstance(response, dict) else {}
    internal_meta = response.get("_internal_meta") if isinstance(response.get("_internal_meta"), dict) else {}
    for candidate in (
        response.get("confidence"),
        internal_meta.get("confidence"),
        assistant_metadata.get("confidence"),
    ):
        if candidate in (None, ""):
            continue
        try:
            return float(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _extract_tool_calls(response: Optional[Dict[str, Any]], assistant_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    response = response if isinstance(response, dict) else {}
    tool_calls = response.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        return [item for item in tool_calls if isinstance(item, dict)]

    raw_metadata_tools = assistant_metadata.get("tool_calls")
    if isinstance(raw_metadata_tools, list) and raw_metadata_tools:
        normalized: List[Dict[str, Any]] = []
        for item in raw_metadata_tools:
            tool_name = _clean_text(item)
            if tool_name:
                normalized.append({"name": tool_name})
        return normalized
    return []


def _extract_response_type(response: Optional[Dict[str, Any]], assistant_metadata: Dict[str, Any]) -> str:
    response = response if isinstance(response, dict) else {}
    context = assistant_metadata.get("context") if isinstance(assistant_metadata.get("context"), dict) else {}
    ui_payload = assistant_metadata.get("ui_payload") if isinstance(assistant_metadata.get("ui_payload"), dict) else {}

    if response.get("chart_data") or response.get("chart_spec") or context.get("has_chart"):
        return "chart"
    if response.get("dashboard_spec") or context.get("has_dashboard"):
        return "dashboard"
    if response.get("table_data") or ui_payload.get("type") == "table":
        return "table"

    response_type = _clean_text(response.get("type") or context.get("response_type") or ui_payload.get("type") or "text")
    return response_type or "text"


def _has_table(response: Optional[Dict[str, Any]], assistant_metadata: Dict[str, Any]) -> bool:
    response = response if isinstance(response, dict) else {}
    ui_payload = assistant_metadata.get("ui_payload") if isinstance(assistant_metadata.get("ui_payload"), dict) else {}
    return bool(response.get("table_data") or ui_payload.get("type") == "table")


def should_capture_chat_example(
    *,
    query: str,
    assistant_text: str,
    source: str,
    mode: str,
    response_type: str,
    has_chart: bool,
    has_dashboard: bool,
    has_table: bool,
    has_image: bool,
    has_audio: bool,
    has_automation: bool,
) -> bool:
    if not _clean_text(query) or not _clean_text(assistant_text):
        return False
    normalized_response = _clean_text(assistant_text).lower()
    if any(marker in normalized_response for marker in _DEGRADED_RESPONSE_MARKERS):
        return False
    normalized_mode = _clean_text(mode).lower()
    if normalized_mode and any(normalized_mode.startswith(prefix) for prefix in _BLOCKED_MODE_PREFIXES):
        return False
    normalized_source = _clean_text(source).lower()
    if normalized_source and any(normalized_source.startswith(prefix) for prefix in _BLOCKED_SOURCE_PREFIXES):
        return False
    if has_image or has_audio or has_automation:
        return False
    if response_type not in _ALLOWED_RESPONSE_TYPES and not (has_chart or has_dashboard or has_table):
        return False
    return True


def _derive_intent(query: str, source: str, response_type: str, tool_calls: List[Dict[str, Any]]) -> str:
    normalized_query = _clean_text(query).lower()
    normalized_source = _clean_text(source).lower()
    tool_names = []
    for item in tool_calls:
        if not isinstance(item, dict):
            continue
        function_obj = item.get("function") if isinstance(item.get("function"), dict) else {}
        tool_name = _clean_text(function_obj.get("name") or item.get("name"))
        if tool_name:
            tool_names.append(tool_name.lower())

    if "mercado" in normalized_query or "concorr" in normalized_query or "pesquisar_mercado" in normalized_source:
        return "market_research"
    if response_type == "dashboard":
        return "dashboard"
    if response_type == "chart":
        return "visualization"
    if any("code_gen" in tool_name or "calcular" in tool_name for tool_name in tool_names):
        return "calculation"
    if "sql" in normalized_query:
        return "sql"
    return "data_query"


def _build_tags(
    *,
    source: str,
    response_type: str,
    assistant_metadata: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    has_chart: bool,
    has_dashboard: bool,
    has_table: bool,
) -> List[str]:
    context = assistant_metadata.get("context") if isinstance(assistant_metadata.get("context"), dict) else {}
    tags: List[str] = []
    for value in (
        response_type,
        source,
        context.get("segment"),
        context.get("une"),
        context.get("market_product_hint"),
    ):
        normalized = _clean_text(value)
        if normalized:
            tags.append(normalized)
    for item in tool_calls:
        if not isinstance(item, dict):
            continue
        function_obj = item.get("function") if isinstance(item.get("function"), dict) else {}
        tool_name = _clean_text(function_obj.get("name") or item.get("name"))
        if tool_name:
            tags.append(tool_name)
    if has_chart:
        tags.append("has_chart")
    if has_dashboard:
        tags.append("has_dashboard")
    if has_table:
        tags.append("has_table")

    deduped: List[str] = []
    seen = set()
    for item in tags:
        normalized = item.lower()
        if normalized in seen:
            continue
        deduped.append(item)
        seen.add(normalized)
    return deduped


def build_chat_example_payload(
    *,
    query: str,
    user_id: str,
    response: Optional[Dict[str, Any]] = None,
    assistant_text: Optional[str] = None,
    assistant_metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    normalized_query = _clean_text(query)
    assistant_metadata = assistant_metadata if isinstance(assistant_metadata, dict) else {}
    context = assistant_metadata.get("context") if isinstance(assistant_metadata.get("context"), dict) else {}
    response = response if isinstance(response, dict) else {}

    normalized_response = _extract_response_text(response, assistant_text)
    source = _extract_source(response, assistant_metadata)
    mode = _extract_mode(response, assistant_metadata)
    confidence = _extract_confidence(response, assistant_metadata)
    response_type = _extract_response_type(response, assistant_metadata)
    has_chart = bool(response.get("chart_data") or response.get("chart_spec") or context.get("has_chart"))
    has_dashboard = bool(response.get("dashboard_spec") or context.get("has_dashboard"))
    has_table = _has_table(response, assistant_metadata)
    has_image = bool(response.get("image_asset") or context.get("has_image"))
    has_audio = bool(response.get("audio_asset") or context.get("has_audio"))
    has_automation = bool(response.get("automation_request") or context.get("has_automation"))
    tool_calls = _extract_tool_calls(response, assistant_metadata)

    if not should_capture_chat_example(
        query=normalized_query,
        assistant_text=normalized_response,
        source=source,
        mode=mode,
        response_type=response_type,
        has_chart=has_chart,
        has_dashboard=has_dashboard,
        has_table=has_table,
        has_image=has_image,
        has_audio=has_audio,
        has_automation=has_automation,
    ):
        return None

    request_id = _clean_text(assistant_metadata.get("request_id") or context.get("request_id"))
    example_id = request_id or hashlib.md5(
        f"{normalized_query}|{normalized_response}|{source}|{response_type}".encode("utf-8")
    ).hexdigest()
    intent = _derive_intent(normalized_query, source, response_type, tool_calls)
    tags = _build_tags(
        source=source,
        response_type=response_type,
        assistant_metadata=assistant_metadata,
        tool_calls=tool_calls,
        has_chart=has_chart,
        has_dashboard=has_dashboard,
        has_table=has_table,
    )
    code = extract_code_blocks(normalized_response)
    capture_metadata: Dict[str, Any] = {
        "request_id": request_id or example_id,
        "source": source,
        "mode": mode,
        "response_type": response_type,
        "tool_calls": tool_calls,
        "tags": tags,
        "has_chart": has_chart,
        "has_dashboard": has_dashboard,
        "has_table": has_table,
        "segment": _clean_text(context.get("segment")),
        "une": _clean_text(context.get("une")),
        "market_product_hint": _clean_text(context.get("market_product_hint")),
        "response_breakdown": _clean_text(context.get("response_breakdown")),
    }
    if confidence is not None:
        capture_metadata["confidence"] = confidence
        capture_metadata["confidence_score"] = confidence

    result_summary = {
        "response_text": normalized_response,
        "response_type": response_type,
        "source": source,
        "confidence": confidence,
        "has_chart": has_chart,
        "has_dashboard": has_dashboard,
        "has_table": has_table,
        "tool_calls": tool_calls,
    }

    return {
        "timestamp": timestamp or datetime.now(),
        "user_id": _clean_text(user_id) or "anonymous",
        "query": normalized_query,
        "code": code,
        "result": result_summary,
        "intent": intent,
        "example_id": example_id,
        "assistant_response": normalized_response,
        "metadata": capture_metadata,
    }
