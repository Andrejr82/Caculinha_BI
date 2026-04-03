from __future__ import annotations

import re
from statistics import median
from typing import Any, Dict, List, Optional

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
    "promocao",
    "promoção",
    "desconto",
    "cesta",
    "cross-sell",
    "cross sell",
    "afinidade",
    "ticket medio",
    "ticket médio",
    "previsao",
    "previsão",
    "sazonal",
    "sazonalidade",
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


def _fmt_currency(value: Any) -> str:
    return f"R$ {_fmt_number(value)}"


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


def _sales_dimension_entity_label(key: str) -> str:
    normalized = _normalize_key(key)
    mapping = {
        "une": "lojas (UNE)",
        "lojaune": "lojas (UNE)",
        "loja": "lojas",
        "nomesegmento": "segmentos",
        "segmento": "segmentos",
        "nomecategoria": "categorias",
        "categoria": "categorias",
        "nomegrupo": "grupos",
        "grupo": "grupos",
        "nomefabricante": "fabricantes",
        "fabricante": "fabricantes",
        "nome": "produtos",
        "produto": "produtos",
    }
    return mapping.get(normalized, _sales_dimension_label(key).lower())


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
    entity_label = _sales_dimension_entity_label(dim_key)

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
        reading = f"há concentração {concentration} entre os principais {entity_label}"
        actions = (
            f"- Priorize os {entity_label} abaixo da mediana para revisão de sortimento, preço e execução comercial.\n"
            f"- Compare os {entity_label} líderes com a cauda para identificar lacunas de mix e demanda.\n"
            "- Reavalie o desempenho no próximo ciclo semanal com o mesmo recorte."
        )

    return (
        "## Resumo executivo\n"
        f"- Consolidado de vendas por {dimension_label.lower()} concluído. No recorte analisado, o total vendido alcançou {_fmt_currency(total_value)}, distribuído em {len(prepared_rows)} {entity_label}.\n"
        f"- Principal contribuição: {leader['label']} com {_fmt_currency(leader['value'])}, equivalente a {leader_share:.1f}% do total.\n"
        f"- Indicadores de distribuição: média de {_fmt_currency(average_value)} por {dimension_label.lower()}, mediana de {_fmt_currency(median_value)}, participação do Top 5 em {top_5_share:.1f}% e da cauda em {bottom_5_share:.1f}%.\n"
        f"- Leitura gerencial: {reading} e a distância entre a maior e a menor posição do recorte é de {_fmt_currency(amplitude)}.\n\n"
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

    recognized_template = classify_business_response_shape(query)["template_id"] != "geral_executivo"
    if not is_business_query(query) and not recognized_template and "## resumo" not in text.lower():
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
        table = _default_table_for_query(query, text)

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


def classify_business_response_shape(query: str) -> Dict[str, str]:
    template = select_official_report_template(query)
    template_id = str(template.get("id") or "geral_executivo")
    process = str(template.get("processo") or "geral")
    return {
        "template_id": template_id,
        "processo": process,
        "nome": str(template.get("nome") or "Executivo Padrao"),
    }


def _default_table_for_query(query: str, message: str) -> str:
    shape = classify_business_response_shape(query)
    template_id = shape["template_id"]
    summary = _first_sentence(message)

    if template_id == "compras_ruptura":
        return (
            "| Frente | Leitura operacional |\n"
            "|---|---|\n"
            f"| Ruptura/Cobertura | {summary} |\n"
            "| Impacto | Validar perda de venda, cobertura em dias e lojas mais afetadas |\n"
            "| Prioridade | Atuar primeiro nos itens com cobertura zerada ou abaixo de 3 dias |"
        )

    if template_id in {"compras_cotacao", "comercial_margem", "comercial_promocao"}:
        return (
            "| Indicador | Leitura |\n"
            "|---|---|\n"
            f"| Diagnostico | {summary} |\n"
            "| Margem/Preco | Confirmar faixa de preco, custo e impacto comercial |\n"
            "| Decisao | Aprovar acao apenas com regra clara de rentabilidade |"
        )

    if template_id == "comercial_cesta":
        return (
            "| Frente | Leitura |\n"
            "|---|---|\n"
            f"| Cesta/Afinidade | {summary} |\n"
            "| Oportunidade | Identificar itens complementares, bundles e ganho de ticket |\n"
            "| Acao | Priorizar combinacoes com maior recorrencia e margem saudavel |"
        )

    if template_id in {"comercial_transferencia", "compras_previsao", "compras_eoq"}:
        return (
            "| Frente | Leitura |\n"
            "|---|---|\n"
            f"| Planejamento | {summary} |\n"
            "| Gap operacional | Validar necessidade, cobertura e capacidade de atendimento |\n"
            "| Acao sugerida | Traduzir a analise em quantidade, prazo e destino prioritario |"
        )

    return (
        "| Indicador | Leitura |\n"
        "|---|---|\n"
        f"| Resumo | {summary} |\n"
        "| Evidencia operacional | Complementar com numeros-chave da consulta |\n"
        "| Proximo passo | Converter a leitura em decisao comercial ou operacional |"
    )


def _default_action_for_query(query: str) -> str:
    q = (query or "").lower()
    template_id = classify_business_response_shape(query)["template_id"]

    if template_id == "compras_ruptura":
        return (
            "- Priorize os itens com cobertura zerada ou abaixo de 3 dias e execute reposição/transferência nas próximas 24h.\n"
            "- Reavalie lojas e SKUs críticos depois da movimentação para confirmar recomposição.\n"
            "- Ajuste ponto de pedido e estoque-alvo dos itens recorrentes para reduzir reincidência."
        )

    if template_id in {"compras_cotacao", "comercial_margem", "comercial_promocao"}:
        return (
            "- Confirme custo, preço atual, desconto e margem real antes de aprovar a ação.\n"
            "- Compare o cenário atual com o cenário proposto e defina limite mínimo de rentabilidade.\n"
            "- Monitore volume, margem e conversão durante a ação para corrigir rapidamente."
        )

    if template_id == "comercial_cesta":
        return (
            "- Priorize os pares ou combos com maior afinidade e melhor margem combinada.\n"
            "- Teste exposição conjunta, bundle ou recomendação assistida nas lojas de maior fluxo.\n"
            "- Reavalie ticket médio e taxa de anexação no próximo ciclo operacional."
        )

    if template_id in {"comercial_transferencia", "compras_previsao", "compras_eoq"}:
        return (
            "- Converta a análise em plano com quantidade, prioridade e prazo por loja ou SKU.\n"
            "- Revise cobertura, excesso e necessidade real antes de comprar ou transferir.\n"
            "- Compare previsto versus realizado no próximo ciclo para calibrar o modelo decisório."
        )

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
