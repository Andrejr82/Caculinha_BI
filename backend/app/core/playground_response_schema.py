from __future__ import annotations

import json


def enforce_playground_response_schema(content: str, json_mode: bool) -> str:
    text = content or ""
    if json_mode:
        try:
            payload = json.loads(text) if text.strip() else {}
        except Exception:
            payload = {"summary": text.strip() or "Resposta gerada.", "table": {"headers": [], "rows": []}, "action": "Revisar saída."}

        summary = str(payload.get("summary") or payload.get("message") or "Resposta gerada.")
        table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
        headers = table.get("headers") if isinstance(table.get("headers"), list) else []
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        action = str(payload.get("action") or "Validar com o analista responsável.")
        normalized = {
            "summary": summary,
            "table": {"headers": headers, "rows": rows},
            "action": action,
        }
        # Preserve useful metadata when present
        for key in ["language", "dialect", "query", "code", "template"]:
            if key in payload:
                normalized[key] = payload[key]
        return json.dumps(normalized, ensure_ascii=False, indent=2)

    required_sections = ["## Resumo", "## Tabela", "## Ação recomendada"]
    if all(section in text for section in required_sections):
        return text

    summary = text.strip() or "Resposta gerada."
    return (
        "## Resumo\n"
        f"{summary}\n\n"
        "## Tabela\n"
        "_Sem tabela estruturada._\n\n"
        "## Ação recomendada\n"
        "Validar e ajustar para o contexto operacional do BI."
    )
