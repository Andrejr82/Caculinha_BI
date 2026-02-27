from __future__ import annotations

import re
from typing import Dict, List

from backend.app.core.utils.report_templates import select_official_report_template


_BUSINESS_KEYWORDS = (
    "venda",
    "estoque",
    "segmento",
    "grupo",
    "une",
    "loja",
    "ruptura",
    "compra",
    "margem",
    "preco",
    "preço",
    "cotacao",
    "cotação",
    "fornecedor",
    "mercado",
    "eoq",
    "demanda",
)


def is_business_query(query: str) -> bool:
    q = (query or "").strip().lower()
    return any(keyword in q for keyword in _BUSINESS_KEYWORDS)


def _extract_section(text: str, headings: List[str]) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    idx = None
    normalized_headings = [h.lower().strip() for h in headings]
    for i, line in enumerate(lines):
        normalized_line = line.lower().strip()
        if normalized_line.startswith("## ") and any(
            normalized_line.startswith(h) for h in normalized_headings
        ):
            idx = i
            break
    if idx is None:
        return ""

    content_lines = []
    for line in lines[idx + 1 :]:
        if line.strip().lower().startswith("## "):
            break
        content_lines.append(line)
    return "\n".join(content_lines).strip()


def _first_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return "Analise concluida."
    match = re.match(r"(.{1,220}?[.!?])(\s|$)", cleaned)
    if match:
        return match.group(1).strip()
    return cleaned[:220].strip()


def ensure_executive_output(query: str, message: str) -> str:
    """
    Garante saida no padrao executivo da Fase 3:
    Resumo, Tabela, SQL/Python, Acao e Recorte/Evidencia.
    """
    text = str(message or "").strip()
    if not text:
        return text

    if not is_business_query(query) and "## resumo" not in text.lower():
        return text

    template = select_official_report_template(query)

    summary = _extract_section(text, ["## resumo executivo", "## resumo"])
    table = _extract_section(text, ["## tabela operacional", "## tabela"])
    sql_python = _extract_section(text, ["## sql/python", "## sql", "## python"])
    action = _extract_section(text, ["## ação recomendada", "## acao recomendada"])
    evidence = _extract_section(text, ["## recorte e evidência", "## recorte e evidencia", "## evidência", "## evidencia"])

    if not summary:
        summary = f"- {_first_sentence(text)}"
    elif not summary.strip().startswith("-"):
        summary = f"- {summary.strip()}"

    if not table:
        table = (
            "| Indicador | Valor |\n"
            "|---|---|\n"
            "| Status | Dados retornados sem tabela estruturada nesta rodada |"
        )

    if not sql_python:
        wants_technical = any(k in (query or "").lower() for k in ("sql", "python", "script", "query"))
        if wants_technical:
            sql_python = (
                "```sql\n"
                "-- Ajuste filtros de periodo/UNE/segmento conforme necessario\n"
                "SELECT *\n"
                "FROM admmat\n"
                "LIMIT 50;\n"
                "```\n\n"
                "```python\n"
                "# Use este bloco como base para validacao rapida\n"
                "df.head(50)\n"
                "```"
            )
        else:
            sql_python = "- Nao aplicavel para esta pergunta (resposta executiva direta)."

    if not action:
        action = "- Priorizar validacao com o time responsavel e executar o proximo passo operacional."
    elif not action.strip().startswith("-"):
        action = f"- {action.strip()}"

    if not evidence:
        evidence = "- Recorte aplicado conforme consulta do usuario; confirme periodo e filtros para auditoria."
    elif not evidence.strip().startswith("-"):
        evidence = f"- {evidence.strip()}"

    template_line = f"- Template oficial: {template['nome']} ({template['processo']})"

    return (
        "## Resumo executivo\n"
        f"{summary}\n"
        f"{template_line}\n\n"
        "## Tabela operacional\n"
        f"{table}\n\n"
        "## SQL/Python\n"
        f"{sql_python}\n\n"
        "## Ação recomendada\n"
        f"{action}\n\n"
        "## Recorte e evidência\n"
        f"{evidence}"
    )


def validate_executive_output(text: str) -> Dict[str, bool]:
    lowered = (text or "").lower()
    return {
        "resumo": "## resumo executivo" in lowered or "## resumo" in lowered,
        "tabela": "## tabela operacional" in lowered or "## tabela" in lowered,
        "sql_python": "## sql/python" in lowered or "## sql" in lowered or "## python" in lowered,
        "acao": "## ação recomendada" in lowered or "## acao recomendada" in lowered,
        "evidencia": "## recorte e evidência" in lowered or "## recorte e evidencia" in lowered,
    }
