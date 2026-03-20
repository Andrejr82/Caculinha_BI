from __future__ import annotations

import re
from typing import Dict, List

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
    Garante saída executiva em linguagem de negócio (sem blocos técnicos).
    """
    text = str(message or "").strip()
    if not text:
        return text

    if not is_business_query(query) and "## resumo" not in text.lower():
        return text

    summary = _extract_section(text, ["## resumo executivo", "## resumo"])
    table = _extract_section(text, ["## tabela operacional", "## tabela"])
    action = _extract_section(
        text,
        ["## próximas ações", "## proximas acoes", "## ação recomendada", "## acao recomendada"],
    )

    if not summary:
        summary = f"- {_first_sentence(text)}"
    elif not summary.strip().startswith("-"):
        summary = f"- {summary.strip()}"

    if not table:
        table = "- Sem dados tabulares adicionais para exibir nesta resposta."

    if not action:
        action = _default_action_for_query(query)
    elif not action.strip().startswith("-"):
        action = f"- {action.strip()}"

    return (
        "## Resumo executivo\n"
        f"{summary}\n"
        "\n"
        "## Tabela operacional\n"
        f"{table}\n\n"
        "## Próximas ações\n"
        f"{action}"
    )


def validate_executive_output(text: str) -> Dict[str, bool]:
    lowered = (text or "").lower()
    return {
        "resumo": "## resumo executivo" in lowered or "## resumo" in lowered,
        "tabela": "## tabela operacional" in lowered or "## tabela" in lowered,
        "acoes": "## próximas ações" in lowered or "## proximas acoes" in lowered or "## ação recomendada" in lowered or "## acao recomendada" in lowered,
    }


def _default_action_for_query(query: str) -> str:
    q = (query or "").lower()
    if any(k in q for k in ["dashboard", "gráfico", "grafico", "vendas", "segmento", "une", "loja"]):
        return (
            "- Priorize as 3 UNEs/segmentos de menor venda com plano comercial em até 7 dias.\n"
            "- Revise ruptura e cobertura de estoque dos itens líderes para sustentar o giro.\n"
            "- Reavalie os KPIs no próximo ciclo (D+7) e ajuste preço/mix conforme resultado."
        )
    if any(k in q for k in ["pesquisa de mercado", "concorrente", "preço", "preco"]):
        return (
            "- Valide as 3 melhores ofertas com cotação direta antes de fechar o pedido.\n"
            "- Negocie com base na mediana de preço e no prazo de entrega.\n"
            "- Reexecute a pesquisa com marca/SKU para aumentar a precisão."
        )
    if any(k in q for k in ["eoq", "lote econômico", "lote economico", "sensibilidade"]):
        return (
            "- Use o lote recomendado como baseline de compra desta semana.\n"
            "- Simule variação de demanda (+/-20%) antes de confirmar o volume final.\n"
            "- Monitore ruptura e giro por 30 dias para recalibrar o parâmetro."
        )
    return "- Execute o próximo passo operacional com base no resumo e valide resultado no próximo ciclo."
