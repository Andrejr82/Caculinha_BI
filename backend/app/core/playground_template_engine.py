from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Optional

from backend.app.core.playground_rules_engine import build_structured_response


TEMPLATES_PATH = Path(__file__).resolve().parent / "prompts" / "bi_templates_catalog.json"


@dataclass(frozen=True)
class PlaygroundTemplateResult:
    matched: bool
    response: str
    source: str
    confidence: float
    intent: str
    template_version: str


def load_bi_templates_catalog() -> dict:
    try:
        with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": "unknown", "templates": []}


def resolve_playground_template(message: str, json_mode: bool = False) -> Optional[PlaygroundTemplateResult]:
    text = (message or "").lower()
    if not text.strip():
        return None

    catalog = load_bi_templates_catalog()
    version = str(catalog.get("version", "unknown"))
    for item in catalog.get("templates", []):
        keywords = [str(k).lower() for k in item.get("keywords", [])]
        if keywords and all(k in text for k in keywords):
            response = build_structured_response(
                json_mode=json_mode,
                summary=str(item.get("summary", "Template BI selecionado.")),
                table_headers=[str(h) for h in item.get("headers", [])],
                table_rows=[[str(c) for c in row] for row in item.get("rows", [])],
                action=str(item.get("action", "Executar revisão analítica.")),
                template=None,
                language=None,
            )
            return PlaygroundTemplateResult(
                matched=True,
                response=response,
                source="template-engine",
                confidence=0.82,
                intent=str(item.get("id", "template.generic")),
                template_version=version,
            )

    return None
