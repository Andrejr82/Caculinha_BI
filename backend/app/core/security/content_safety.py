import re
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1F\x7F]")
_DANGEROUS_TEXT_PATTERNS = (
    re.compile(r"(?i)<\s*script\b"),
    re.compile(r"(?i)<\s*iframe\b"),
    re.compile(r"(?i)\bon\w+\s*="),
    re.compile(r"(?i)\b(?:javascript|vbscript|data)\s*:"),
)
_DANGEROUS_COMMAND_PATTERNS = (
    re.compile(r"`"),
    re.compile(r"\$\("),
    re.compile(r"(?i)(?:^|[\s;|&])(?:cmd(?:\.exe)?|powershell|pwsh|bash|sh|curl|wget)\b"),
    re.compile(r"(?i)\b(?:rm\s+-rf|del\s+/f|format\s+[a-z]:|shutdown\s+/s)\b"),
    re.compile(r"(?:&&|\|\||;|>>|<<)"),
    re.compile(r"\.\./"),
)
_DEFAULT_ALLOWED_AUTOMATION_ACTIONS = {
    "browser.navigate",
    "browser.extract",
    "spreadsheet.create_report",
    "spreadsheet.update_cells",
    "export.csv",
    "email.draft",
    "email.send",
    "message.draft",
    "message.send",
}


def sanitize_text_label(value: Any, *, max_length: int = 160) -> str:
    raw = unescape(str(value or ""))
    raw = _HTML_TAG_RE.sub("", raw)
    raw = _CONTROL_CHAR_RE.sub(" ", raw)
    raw = " ".join(raw.split())
    if not raw:
        return ""
    return raw[:max_length]


def sanitize_public_url(value: Any, *, allow_internal_download: bool = False) -> str:
    raw = str(value or "").strip()
    if not raw or _CONTROL_CHAR_RE.search(raw):
        return ""

    parsed = urlparse(raw)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return raw

    if allow_internal_download and raw.startswith("/api/v1/chat/market-research/download/"):
        return raw

    return ""


def sanitize_citation(citation: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(citation, dict):
        return None

    sanitized: Dict[str, Any] = {}
    source = sanitize_text_label(citation.get("source"))
    domain = sanitize_text_label(citation.get("domain"), max_length=80)
    competitor = sanitize_text_label(citation.get("competitor"), max_length=80)
    document_id = sanitize_text_label(citation.get("document_id"), max_length=120)
    url = sanitize_public_url(citation.get("url"))

    if source:
        sanitized["source"] = source
    if domain:
        sanitized["domain"] = domain
    if competitor:
        sanitized["competitor"] = competitor
    if document_id:
        sanitized["document_id"] = document_id
    if url:
        sanitized["url"] = url

    return sanitized or None


def sanitize_citations(citations: Any, *, limit: int = 8) -> List[Dict[str, Any]]:
    if not isinstance(citations, list):
        return []

    sanitized_items: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for raw_item in citations:
        sanitized = sanitize_citation(raw_item)
        if not sanitized:
            continue
        dedupe_key = "|".join(
            [
                str(sanitized.get("source") or ""),
                str(sanitized.get("domain") or ""),
                str(sanitized.get("url") or ""),
                str(sanitized.get("document_id") or ""),
            ]
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        sanitized_items.append(sanitized)
        if len(sanitized_items) >= max(1, int(limit)):
            break
    return sanitized_items


def validate_upload_filename(filename: Any) -> str:
    raw = str(filename or "").strip()
    if not raw:
        raise ValueError("Nome de arquivo inválido")
    if raw.startswith(".") or raw in {".", ".."}:
        raise ValueError("Nome de arquivo inválido")
    if raw != Path(raw).name:
        raise ValueError("Nome de arquivo inválido")
    if ".." in raw or _CONTROL_CHAR_RE.search(raw):
        raise ValueError("Nome de arquivo inválido")

    safe_name = sanitize_text_label(raw, max_length=180)
    if not safe_name:
        raise ValueError("Nome de arquivo inválido")
    return safe_name


def contains_dangerous_text_payload(value: Any) -> bool:
    text = str(value or "")
    return any(pattern.search(text) for pattern in _DANGEROUS_TEXT_PATTERNS)


def validate_automation_action(
    action_payload: Any,
    *,
    allowed_actions: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    if not isinstance(action_payload, dict):
        raise ValueError("Ação de automação inválida")

    action_name = sanitize_text_label(action_payload.get("action"), max_length=80).lower()
    if not action_name:
        raise ValueError("Ação de automação inválida")

    allowed = {str(item).strip().lower() for item in (allowed_actions or _DEFAULT_ALLOWED_AUTOMATION_ACTIONS)}
    if action_name not in allowed:
        raise ValueError("Ação de automação não autorizada")

    params = action_payload.get("params")
    normalized_params = params if isinstance(params, dict) else {}
    _assert_safe_automation_payload(normalized_params)
    return {"action": action_name, "params": normalized_params}


def _assert_safe_automation_payload(value: Any) -> None:
    if isinstance(value, str):
        normalized = " ".join(value.split())
        if any(pattern.search(normalized) for pattern in _DANGEROUS_COMMAND_PATTERNS):
            raise ValueError("Comando de automação bloqueado")
        return
    if isinstance(value, dict):
        for nested in value.values():
            _assert_safe_automation_payload(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _assert_safe_automation_payload(nested)
