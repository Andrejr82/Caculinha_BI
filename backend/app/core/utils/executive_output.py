from __future__ import annotations

import re
from statistics import median
from typing import Any, Dict, List, Optional

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


def _normalize_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key or "").strip().lower())


def _to_float(value: Any) -> float:
    if value in (None, "", []):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    text = text.replace("R$", "").replace("%", "").replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _fmt_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value or "-").strip() or "-"
    if abs(number - round(number)) < 1e-9:
        return str(int(round(number)))
    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _find_first_key(row: Dict[str, Any], aliases: List[str]) -> Optional[str]:
    normalized_aliases = {_normalize_key(alias) for alias in aliases}
    for key in row.keys():
        if _normalize_key(key) in normalized_aliases:
            return key
    return None


def _sales_dimension_label(key: str) -> str:
    normalized = _normalize_key(key)
    mapping = {
        "une": "Loja (UNE)",
        "lojaune": "Loja (UNE)",
        "loja": "Loja",
        "nomesegmento": "Segmento",
        "segmento": "Segmento",
        "nomecategoria": "Categoria",
        "categoria": "Categoria",
        "nomegrupo": "Grupo",
        "grupo": "Grupo",
        "nomefabricante": "Fabricante",
        "fabricante": "Fabricante",
        "nome": "Produto",
        "produto": "Produto",
    }
    return mapping.get(normalized, str(key or "Dimensão").replace("_", " ").title())


def build_sales_dimension_report_from_rows(query: str, rows: List[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(rows, list) or not rows:
        return None

    q = (query or "").lower()
    if "venda" not in q and "relatório" not in q and "relatorio" not in q:
        return None

    first_row = next((row for row in rows if isinstance(row, dict) and row), None)
    if not first_row:
        return None

    dim_key = _find_first_key(
        first_row,
        [
            "UNE",
            "Loja (UNE)",
            "loja",
            "NOMESEGMENTO",
            "segmento",
            "NOMECATEGORIA",
            "categoria",
            "NOMEGRUPO",
            "grupo",
            "NOMEFABRICANTE",
            "fabricante",
            "NOME",
            "produto",
        ],
    )
    value_key = _find_first_key(
        first_row,
        [
            "TOTAL_VENDAS",
            "valor",
            "Venda (R$)",
            "venda",
            "VENDA_30DD",
            "vendas_30d",
            "total",
        ],
    )
    if not dim_key or not value_key:
        return None

    prepared_rows: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = str(row.get(dim_key) or "").strip() or "N/A"
        value = _to_float(row.get(value_key))
        prepared_rows.append({"label": label, "value": value})

    prepared_rows = [row for row in prepared_rows if row["label"] != "N/A" or row["value"] > 0]
    if not prepared_rows:
        return None

    prepared_rows.sort(key=lambda item: item["value"], reverse=True)
    values = [row["value"] for row in prepared_rows]
    total_value = sum(values)
    if total_value <= 0:
        return None

    average_value = total_value / len(prepared_rows)
    median_value = median(values)
    top_5_share = (sum(values[:5]) / total_value) * 100.0
    bottom_5_share = (sum(values[-5:]) / total_value) * 100.0
    leader = prepared_rows[0]
    leader_share = (leader["value"] / total_value) * 100.0
    amplitude = leader["value"] - values[-1]
    concentration = "alta" if leader_share >= 25 or top_5_share >= 65 else "moderada" if leader_share >= 15 or top_5_share >= 45 else "baixa"
    dimension_label = _sales_dimension_label(dim_key)

    enriched_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(prepared_rows, start=1):
        share_pct = (row["value"] / total_value) * 100.0
        gap_media = row["value"] - average_value
        if row["value"] >= average_value * 1.2:
            classification = "liderança" if index <= 3 else "acima da média"
        elif row["value"] <= average_value * 0.8:
            classification = "cauda" if index > max(5, len(prepared_rows) - 3) else "abaixo da média"
        else:
            classification = "na média"
        enriched_rows.append(
            {
                "label": row["label"],
                "value": row["value"],
                "share_pct": share_pct,
                "rank": index,
                "gap_media": gap_media,
                "classification": classification,
            }
        )

    header = f"| {dimension_label} | Venda (R$) | Part. % | Ranking | Gap p/ média (R$) | Classificação |"
    sep = "|---|---|---|---|---|---|"
    body = "\n".join(
        f"| {row['label']} | {_fmt_number(row['value'])} | {row['share_pct']:.1f}% | {row['rank']} | {_fmt_number(row['gap_media'])} | {row['classification']} |"
        for row in enriched_rows[:10]
    )
    if len(enriched_rows) > 10:
        body += f"\n... (+{len(enriched_rows) - 10} linhas)"

    if "segment" in _normalize_key(dim_key):
        reading = f"há concentração {concentration} entre os principais segmentos"
        actions = (
            "- Priorize os segmentos abaixo da mediana para revisão de sortimento, preço e execução comercial.\n"
            "- Compare os segmentos líderes com a cauda para identificar lacunas de mix e demanda.\n"
            "- Reavalie o desempenho no próximo ciclo semanal com o mesmo recorte."
        )
    elif _normalize_key(dim_key) in {"une", "lojaune", "loja"}:
        reading = f"a distribuição está {concentration}mente concentrada nas posições líderes"
        actions = (
            "- Priorize as lojas abaixo da mediana com revisão de mix, preço e execução comercial em até 7 dias.\n"
            "- Compare Top 5 e Bottom 5 para validar ruptura, exposição e profundidade de sortimento.\n"
            "- Reavalie o segmento no próximo ciclo semanal para medir ganho de cobertura e venda."
        )
    else:
        reading = f"há concentração {concentration} entre os principais {dimension_label.lower()}"
        actions = (
            f"- Priorize os {dimension_label.lower()} abaixo da mediana para revisão de sortimento, preço e execução comercial.\n"
            f"- Compare os {dimension_label.lower()} líderes com a cauda para identificar lacunas de mix e demanda.\n"
            "- Reavalie o desempenho no próximo ciclo semanal com o mesmo recorte."
        )

    return (
        "## Resumo executivo\n"
        f"- Consolidado de vendas por {dimension_label.lower()} concluído. Total vendido: {_fmt_number(total_value)} em {len(prepared_rows)} {dimension_label.lower()} analisados.\n"
        f"- Destaque: {leader['label']} lidera com {_fmt_number(leader['value'])} e participação de {leader_share:.1f}% no total.\n"
        f"- KPIs-chave: média de {_fmt_number(average_value)} por {dimension_label.lower()}, mediana de {_fmt_number(median_value)}, participação do Top 5 em {top_5_share:.1f}% e da cauda em {bottom_5_share:.1f}%.\n"
        f"- Leitura gerencial: {reading}; a amplitude entre líder e última posição é de {_fmt_number(amplitude)}. Recorte solicitado: {query.strip()}.\n\n"
        "## Tabela operacional\n"
        f"{header}\n{sep}\n{body}\n\n"
        "## Próximas ações\n"
        f"{actions}"
    )


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
