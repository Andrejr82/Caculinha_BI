"""
Shared helpers for structured business contracts returned by the LLM.

Groq + Llama currently relies on JSON Object Mode for these post-processing
steps, so validation stays local and deterministic.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


BUSINESS_CONTRACT_RESPONSE_FORMAT: Dict[str, str] = {"type": "json_object"}


def normalize_business_contract(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return None

    if not isinstance(payload, dict):
        return None

    headline = str(payload.get("headline") or "").strip()[:240]
    summary = str(payload.get("summary") or "").strip()[:900]
    key_findings = _normalize_text_list(payload.get("key_findings"), limit=5, item_limit=220)
    recommended_actions = _normalize_text_list(
        payload.get("recommended_actions"),
        limit=5,
        item_limit=220,
    )

    if not headline and not summary and not key_findings and not recommended_actions:
        return None

    return {
        "headline": headline,
        "summary": summary,
        "key_findings": key_findings,
        "recommended_actions": recommended_actions,
    }


def _normalize_text_list(value: Any, *, limit: int, item_limit: int) -> List[str]:
    if not isinstance(value, list):
        return []

    normalized: List[str] = []
    for item in value:
        text = str(item or "").strip()
        if not text:
            continue
        normalized.append(text[:item_limit])
        if len(normalized) >= limit:
            break
    return normalized
