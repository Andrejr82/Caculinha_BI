"""
Basket Tools - Calculos deterministicos para cesta, promocao e margem real.

Ferramentas voltadas para:
- Analise completa de carrinho/cesta comercial
- Simulacao de desconto e promocao
- Mineracao de produtos que saem juntos (market basket)
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from itertools import combinations
from typing import Any, Dict, List, Optional

import pandas as pd
from langchain.tools import tool

logger = logging.getLogger(__name__)

TWOPLACES = Decimal("0.01")
HUNDRED = Decimal("100")

try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder

    MLXTEND_AVAILABLE = True
except ImportError:
    apriori = None
    association_rules = None
    TransactionEncoder = None
    MLXTEND_AVAILABLE = False


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if value in (None, "", False):
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(",", ".").strip())
    except (InvalidOperation, ValueError, AttributeError):
        return Decimal(default)


def _money(value: Decimal) -> float:
    return float(value.quantize(TWOPLACES, rounding=ROUND_HALF_UP))


def _percent(value: Decimal) -> float:
    return float(value.quantize(TWOPLACES, rounding=ROUND_HALF_UP))


def _first_of(payload: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return default


def _normalize_items(itens: Any) -> List[Dict[str, Any]]:
    if itens in (None, ""):
        return []
    if isinstance(itens, str):
        try:
            itens = json.loads(itens)
        except json.JSONDecodeError:
            return []
    if not isinstance(itens, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for item in itens:
        if isinstance(item, dict):
            normalized.append(dict(item))
    return normalized


def _normalize_transactions(transacoes: Any) -> List[List[str]]:
    if transacoes in (None, ""):
        return []
    if isinstance(transacoes, str):
        try:
            transacoes = json.loads(transacoes)
        except json.JSONDecodeError:
            return []
    normalized: List[List[str]] = []
    if not isinstance(transacoes, list):
        return normalized
    for tx in transacoes:
        if isinstance(tx, dict):
            itens = tx.get("itens") or tx.get("items") or tx.get("produtos")
            if isinstance(itens, list):
                values = [str(v).strip() for v in itens if str(v).strip()]
                if values:
                    normalized.append(values)
        elif isinstance(tx, list):
            values = [str(v).strip() for v in tx if str(v).strip()]
            if values:
                normalized.append(values)
    return normalized


def _build_item_breakdown(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    sku = str(_first_of(item, "sku", "produto_id", "product_id", default=f"ITEM-{index}"))
    nome = str(_first_of(item, "nome", "name", "produto", "descricao", default=sku))
    quantidade = _to_decimal(_first_of(item, "quantidade", "qty", "quantity", default=1), "1")
    preco_unitario = _to_decimal(_first_of(item, "preco_unitario", "unit_price", "preco", "price"), "0")
    custo_unitario = _to_decimal(_first_of(item, "custo_unitario", "unit_cost", "custo", "cost"), "0")

    receita_bruta = quantidade * preco_unitario

    desconto_pct = _to_decimal(
        _first_of(item, "desconto_pct", "discount_pct", "desconto_percentual", default=0)
    )
    desconto_valor = _to_decimal(
        _first_of(item, "desconto_valor", "discount_value", "desconto", default=0)
    )
    if desconto_pct:
        desconto_valor += (receita_bruta * desconto_pct / HUNDRED)

    receita_liquida = max(Decimal("0"), receita_bruta - desconto_valor)
    custo_mercadoria = quantidade * custo_unitario

    imposto_pct = _to_decimal(_first_of(item, "imposto_pct", "tax_pct", "aliquota_imposto", default=0))
    imposto_valor = _to_decimal(_first_of(item, "imposto_valor", "tax_value", default=0))
    if imposto_pct:
        imposto_valor += receita_liquida * imposto_pct / HUNDRED

    frete_valor = _to_decimal(_first_of(item, "frete_valor", "freight_value", default=0))
    despesa_variavel_pct = _to_decimal(
        _first_of(item, "despesa_variavel_pct", "variable_expense_pct", "comissao_pct", default=0)
    )
    despesa_variavel_valor = _to_decimal(
        _first_of(item, "despesa_variavel_valor", "variable_expense_value", "comissao_valor", default=0)
    )
    if despesa_variavel_pct:
        despesa_variavel_valor += receita_liquida * despesa_variavel_pct / HUNDRED

    custo_fixo_rateado = _to_decimal(_first_of(item, "custo_fixo_rateado", "fixed_cost_alloc", default=0))

    margem_bruta_valor = receita_liquida - custo_mercadoria
    margem_real_valor = (
        receita_liquida
        - custo_mercadoria
        - imposto_valor
        - frete_valor
        - despesa_variavel_valor
        - custo_fixo_rateado
    )

    margem_bruta_pct = (margem_bruta_valor / receita_liquida * HUNDRED) if receita_liquida > 0 else Decimal("0")
    margem_real_pct = (margem_real_valor / receita_liquida * HUNDRED) if receita_liquida > 0 else Decimal("0")

    severidade = "saudavel"
    if margem_real_valor < 0:
        severidade = "negativa"
    elif margem_real_pct < Decimal("5"):
        severidade = "critica"
    elif margem_real_pct < Decimal("12"):
        severidade = "apertada"

    return {
        "sku": sku,
        "nome": nome,
        "quantidade": float(quantidade),
        "preco_unitario": _money(preco_unitario),
        "custo_unitario": _money(custo_unitario),
        "receita_bruta": _money(receita_bruta),
        "desconto_total": _money(desconto_valor),
        "receita_liquida": _money(receita_liquida),
        "custo_mercadoria": _money(custo_mercadoria),
        "impostos": _money(imposto_valor),
        "frete_rateado": _money(frete_valor),
        "despesas_variaveis": _money(despesa_variavel_valor),
        "custos_fixos_rateados": _money(custo_fixo_rateado),
        "margem_bruta_valor": _money(margem_bruta_valor),
        "margem_bruta_pct": _percent(margem_bruta_pct),
        "margem_real_valor": _money(margem_real_valor),
        "margem_real_pct": _percent(margem_real_pct),
        "status_margem": severidade,
    }


def _summarize_items(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "totais": {
                "itens": 0,
                "receita_bruta": 0.0,
                "descontos": 0.0,
                "receita_liquida": 0.0,
                "custo_mercadoria": 0.0,
                "impostos": 0.0,
                "frete_rateado": 0.0,
                "despesas_variaveis": 0.0,
                "custos_fixos_rateados": 0.0,
                "margem_bruta_valor": 0.0,
                "margem_bruta_pct": 0.0,
                "margem_real_valor": 0.0,
                "margem_real_pct": 0.0,
            },
            "itens_criticos": [],
            "alertas": ["Nenhum item valido informado para analise."],
        }

    df = pd.DataFrame(rows)
    receita_liquida = _to_decimal(df["receita_liquida"].sum())
    margem_bruta = _to_decimal(df["margem_bruta_valor"].sum())
    margem_real = _to_decimal(df["margem_real_valor"].sum())

    totais = {
        "itens": int(len(rows)),
        "receita_bruta": _money(_to_decimal(df["receita_bruta"].sum())),
        "descontos": _money(_to_decimal(df["desconto_total"].sum())),
        "receita_liquida": _money(receita_liquida),
        "custo_mercadoria": _money(_to_decimal(df["custo_mercadoria"].sum())),
        "impostos": _money(_to_decimal(df["impostos"].sum())),
        "frete_rateado": _money(_to_decimal(df["frete_rateado"].sum())),
        "despesas_variaveis": _money(_to_decimal(df["despesas_variaveis"].sum())),
        "custos_fixos_rateados": _money(_to_decimal(df["custos_fixos_rateados"].sum())),
        "margem_bruta_valor": _money(margem_bruta),
        "margem_bruta_pct": _percent((margem_bruta / receita_liquida * HUNDRED) if receita_liquida > 0 else Decimal("0")),
        "margem_real_valor": _money(margem_real),
        "margem_real_pct": _percent((margem_real / receita_liquida * HUNDRED) if receita_liquida > 0 else Decimal("0")),
    }

    itens_criticos = [
        {
            "sku": row["sku"],
            "nome": row["nome"],
            "margem_real_valor": row["margem_real_valor"],
            "margem_real_pct": row["margem_real_pct"],
            "status_margem": row["status_margem"],
        }
        for row in rows
        if row["status_margem"] in {"negativa", "critica", "apertada"}
    ]
    itens_criticos.sort(key=lambda row: (row["margem_real_valor"], row["margem_real_pct"]))

    alertas: List[str] = []
    if any(row["status_margem"] == "negativa" for row in rows):
        alertas.append("Ha itens com margem real negativa na cesta.")
    if totais["descontos"] > 0 and totais["margem_real_pct"] < 10:
        alertas.append("O desconto aplicado deixou a margem real da cesta apertada.")
    if totais["frete_rateado"] > 0 and totais["margem_real_pct"] < totais["margem_bruta_pct"]:
        alertas.append("Frete e encargos estao corroendo parte relevante da margem.")

    return {
        "totais": totais,
        "itens_criticos": itens_criticos[:10],
        "alertas": alertas,
    }


def _break_even_uplift_pct(before_margin: Decimal, after_margin: Decimal) -> Optional[float]:
    if before_margin <= 0:
        return 0.0
    if after_margin <= 0:
        return None
    uplift = ((before_margin / after_margin) - Decimal("1")) * HUNDRED
    return _percent(uplift)


def analyze_basket_logic(itens: Any) -> Dict[str, Any]:
    normalized_items = _normalize_items(itens)
    if not normalized_items:
        return {
            "needs_input": True,
            "missing_fields": ["itens"],
            "expected_schema": {
                "itens": [
                    {
                        "sku": "ABC-1",
                        "nome": "Produto A",
                        "quantidade": 3,
                        "preco_unitario": 19.9,
                        "custo_unitario": 11.5,
                        "desconto_pct": 5,
                        "imposto_pct": 8,
                        "frete_valor": 2.5,
                        "despesa_variavel_pct": 3,
                    }
                ]
            },
            "message": "Para calcular margem real da cesta eu preciso da lista de itens com quantidade, preco e custo. Posso receber isso em JSON.",
        }

    rows = [_build_item_breakdown(item, index) for index, item in enumerate(normalized_items, start=1)]
    summary = _summarize_items(rows)
    return {
        "resumo_executivo": (
            f"Cesta com receita liquida de R$ {summary['totais']['receita_liquida']:.2f} e "
            f"margem real de {summary['totais']['margem_real_pct']:.2f}%."
        ),
        **summary,
        "itens": rows,
        "metodologia": {
            "motor": "deterministico_decimal",
            "criterio_margem_real": "receita liquida - custo mercadoria - impostos - frete - despesas variaveis - custos fixos rateados",
        },
    }


def _apply_promotion(
    itens: List[Dict[str, Any]],
    tipo_promocao: str,
    desconto_pct: Optional[float],
    desconto_valor: Optional[float],
    produto_ids_alvo: Optional[List[str]],
    compre_x: Optional[int],
    pague_y: Optional[int],
) -> List[Dict[str, Any]]:
    if not itens:
        return []

    cloned = deepcopy(itens)
    targets = {str(v) for v in (produto_ids_alvo or [])}
    is_targeted = bool(targets)

    def _target(item: Dict[str, Any]) -> bool:
        if not is_targeted:
            return True
        sku = str(_first_of(item, "sku", "produto_id", "product_id", default=""))
        return sku in targets

    if tipo_promocao == "percentual" and desconto_pct:
        for item in cloned:
            if _target(item):
                atual = _to_decimal(_first_of(item, "desconto_pct", "discount_pct", default=0))
                item["desconto_pct"] = float(atual + Decimal(str(desconto_pct)))
        return cloned

    if tipo_promocao == "valor_fixo" and desconto_valor:
        elegiveis = [item for item in cloned if _target(item)]
        if not elegiveis:
            return cloned
        gross_values = []
        total_bruto = Decimal("0")
        for item in elegiveis:
            quantidade = _to_decimal(_first_of(item, "quantidade", "qty", "quantity", default=1), "1")
            preco = _to_decimal(_first_of(item, "preco_unitario", "unit_price", "preco", default=0))
            bruto = quantidade * preco
            gross_values.append(bruto)
            total_bruto += bruto
        total_desconto = Decimal(str(desconto_valor))
        for item, bruto in zip(elegiveis, gross_values):
            rateio = total_desconto if total_bruto <= 0 else (total_desconto * bruto / total_bruto)
            atual = _to_decimal(_first_of(item, "desconto_valor", "discount_value", default=0))
            item["desconto_valor"] = float(atual + rateio)
        return cloned

    if tipo_promocao == "leve_x_pague_y" and compre_x and pague_y is not None and pague_y < compre_x:
        for item in cloned:
            if not _target(item):
                continue
            quantidade = int(_to_decimal(_first_of(item, "quantidade", "qty", "quantity", default=1), "1"))
            preco = _to_decimal(_first_of(item, "preco_unitario", "unit_price", "preco", default=0))
            grupos = quantidade // int(compre_x)
            unidades_gratis = grupos * max(0, int(compre_x) - int(pague_y))
            adicional = preco * Decimal(unidades_gratis)
            atual = _to_decimal(_first_of(item, "desconto_valor", "discount_value", default=0))
            item["desconto_valor"] = float(atual + adicional)
        return cloned

    return cloned


def simulate_promotion_logic(
    itens: Any,
    tipo_promocao: str = "percentual",
    desconto_pct: Optional[float] = None,
    desconto_valor: Optional[float] = None,
    produto_ids_alvo: Optional[List[str]] = None,
    uplift_estimado_pct: float = 0.0,
    compre_x: Optional[int] = None,
    pague_y: Optional[int] = None,
) -> Dict[str, Any]:
    normalized_items = _normalize_items(itens)
    if not normalized_items:
        return {
            "needs_input": True,
            "missing_fields": ["itens"],
            "message": "Para simular promocao eu preciso dos itens da cesta. Posso receber os itens em JSON e o desconto em percentual ou valor.",
        }

    baseline = analyze_basket_logic(normalized_items)
    promoted_items = _apply_promotion(
        normalized_items,
        tipo_promocao=tipo_promocao,
        desconto_pct=desconto_pct,
        desconto_valor=desconto_valor,
        produto_ids_alvo=produto_ids_alvo,
        compre_x=compre_x,
        pague_y=pague_y,
    )
    simulated = analyze_basket_logic(promoted_items)

    before_margin = _to_decimal(baseline["totais"]["margem_real_valor"])
    after_margin = _to_decimal(simulated["totais"]["margem_real_valor"])
    uplift_pct = _to_decimal(uplift_estimado_pct)

    lucro_com_uplift = after_margin * (Decimal("1") + uplift_pct / HUNDRED)
    break_even = _break_even_uplift_pct(before_margin, after_margin)

    return {
        "cenario": {
            "tipo_promocao": tipo_promocao,
            "desconto_pct": desconto_pct,
            "desconto_valor": desconto_valor,
            "produto_ids_alvo": produto_ids_alvo or [],
            "uplift_estimado_pct": float(uplift_pct),
            "compre_x": compre_x,
            "pague_y": pague_y,
        },
        "antes": baseline["totais"],
        "depois": simulated["totais"],
        "delta": {
            "receita_liquida": round(simulated["totais"]["receita_liquida"] - baseline["totais"]["receita_liquida"], 2),
            "margem_real_valor": round(simulated["totais"]["margem_real_valor"] - baseline["totais"]["margem_real_valor"], 2),
            "margem_real_pct": round(simulated["totais"]["margem_real_pct"] - baseline["totais"]["margem_real_pct"], 2),
        },
        "uplift_necessario_para_empatar_pct": break_even,
        "margem_real_com_uplift_estimado": _money(lucro_com_uplift),
        "resumo_executivo": (
            f"A promocao reduz a margem real da cesta de {baseline['totais']['margem_real_pct']:.2f}% "
            f"para {simulated['totais']['margem_real_pct']:.2f}%."
        ),
        "alertas": simulated["alertas"],
        "itens_criticos": simulated["itens_criticos"],
    }


def _mine_market_basket_fallback(
    transacoes: List[List[str]],
    suporte_minimo: float,
    confianca_minima: float,
    lift_minimo: float,
    max_resultados: int,
) -> Dict[str, Any]:
    total = len(transacoes)
    item_counter: Counter[str] = Counter()
    pair_counter: Counter[tuple[str, str]] = Counter()

    for tx in transacoes:
        unique_items = sorted(set(tx))
        item_counter.update(unique_items)
        pair_counter.update(combinations(unique_items, 2))

    regras = []
    for (a, b), pair_count in pair_counter.items():
        support = pair_count / total
        if support < suporte_minimo:
            continue
        support_a = item_counter[a] / total
        support_b = item_counter[b] / total
        confidence_ab = pair_count / item_counter[a]
        confidence_ba = pair_count / item_counter[b]
        lift_ab = confidence_ab / support_b if support_b > 0 else 0.0
        lift_ba = confidence_ba / support_a if support_a > 0 else 0.0

        if confidence_ab >= confianca_minima and lift_ab >= lift_minimo:
            regras.append(
                {
                    "antecedente": [a],
                    "consequente": [b],
                    "support": round(support, 4),
                    "confidence": round(confidence_ab, 4),
                    "lift": round(lift_ab, 4),
                }
            )
        if confidence_ba >= confianca_minima and lift_ba >= lift_minimo:
            regras.append(
                {
                    "antecedente": [b],
                    "consequente": [a],
                    "support": round(support, 4),
                    "confidence": round(confidence_ba, 4),
                    "lift": round(lift_ba, 4),
                }
            )

    regras.sort(key=lambda row: (row["lift"], row["confidence"], row["support"]), reverse=True)
    return {
        "metodo": "fallback_pairs",
        "total_transacoes": total,
        "regras_associacao": regras[:max_resultados],
        "itemsets_frequentes": [
            {"itemset": [item], "support": round(count / total, 4)}
            for item, count in item_counter.most_common(max_resultados)
            if (count / total) >= suporte_minimo
        ],
    }


def mine_market_basket_logic(
    transacoes: Any,
    suporte_minimo: float = 0.05,
    confianca_minima: float = 0.2,
    lift_minimo: float = 1.0,
    max_resultados: int = 20,
) -> Dict[str, Any]:
    normalized_transactions = _normalize_transactions(transacoes)
    if not normalized_transactions:
        return {
            "needs_input": True,
            "missing_fields": ["transacoes"],
            "message": "Para descobrir itens que saem juntos eu preciso de transacoes, por exemplo [['cafe', 'leite'], ['cafe', 'pao']].",
        }

    if not MLXTEND_AVAILABLE:
        return _mine_market_basket_fallback(
            normalized_transactions,
            suporte_minimo=suporte_minimo,
            confianca_minima=confianca_minima,
            lift_minimo=lift_minimo,
            max_resultados=max_resultados,
        )

    encoder = TransactionEncoder()
    array = encoder.fit(normalized_transactions).transform(normalized_transactions)
    df = pd.DataFrame(array, columns=encoder.columns_)

    frequent_itemsets = apriori(df, min_support=suporte_minimo, use_colnames=True)
    if frequent_itemsets.empty:
        return {
            "metodo": "mlxtend_apriori",
            "total_transacoes": len(normalized_transactions),
            "regras_associacao": [],
            "itemsets_frequentes": [],
        }

    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=confianca_minima)
    if not rules.empty:
        rules = rules[rules["lift"] >= lift_minimo].copy()
        rules.sort_values(["lift", "confidence", "support"], ascending=False, inplace=True)

    top_rules = []
    for _, row in rules.head(max_resultados).iterrows():
        top_rules.append(
            {
                "antecedente": sorted(str(v) for v in row["antecedents"]),
                "consequente": sorted(str(v) for v in row["consequents"]),
                "support": round(float(row["support"]), 4),
                "confidence": round(float(row["confidence"]), 4),
                "lift": round(float(row["lift"]), 4),
            }
        )

    frequent_rows = []
    for _, row in frequent_itemsets.sort_values(["support"], ascending=False).head(max_resultados).iterrows():
        frequent_rows.append(
            {
                "itemset": sorted(str(v) for v in row["itemsets"]),
                "support": round(float(row["support"]), 4),
            }
        )

    return {
        "metodo": "mlxtend_apriori",
        "total_transacoes": len(normalized_transactions),
        "regras_associacao": top_rules,
        "itemsets_frequentes": frequent_rows,
    }


@tool
def analisar_cesta_compras(itens: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analisa uma cesta/carrinho comercial com calculo deterministico de margem real.
    USE QUANDO: O usuario pedir margem real da cesta, rentabilidade do carrinho,
    impacto de frete/impostos/despesas ou leitura completa de um pedido com multiplos itens.
    """
    return analyze_basket_logic(itens)


@tool
def simular_promocao_cesta(
    itens: List[Dict[str, Any]],
    tipo_promocao: str = "percentual",
    desconto_pct: Optional[float] = None,
    desconto_valor: Optional[float] = None,
    produto_ids_alvo: Optional[List[str]] = None,
    uplift_estimado_pct: float = 0.0,
    compre_x: Optional[int] = None,
    pague_y: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Simula o impacto de desconto/promocao na cesta.
    USE QUANDO: O usuario perguntar sobre impacto de desconto, promocao,
    leve x pague y, quebra de margem ou volume adicional necessario para compensar a oferta.
    """
    return simulate_promotion_logic(
        itens=itens,
        tipo_promocao=tipo_promocao,
        desconto_pct=desconto_pct,
        desconto_valor=desconto_valor,
        produto_ids_alvo=produto_ids_alvo,
        uplift_estimado_pct=uplift_estimado_pct,
        compre_x=compre_x,
        pague_y=pague_y,
    )


@tool
def minerar_cestas_frequentes(
    transacoes: List[List[str]],
    suporte_minimo: float = 0.05,
    confianca_minima: float = 0.2,
    lift_minimo: float = 1.0,
    max_resultados: int = 20,
) -> Dict[str, Any]:
    """
    Minera itens que saem juntos usando market basket / regras de associacao.
    USE QUANDO: O usuario perguntar o que vende junto, afinidade entre itens,
    produtos comprados juntos, cross-sell ou cesta de compras recorrente.
    """
    return mine_market_basket_logic(
        transacoes=transacoes,
        suporte_minimo=suporte_minimo,
        confianca_minima=confianca_minima,
        lift_minimo=lift_minimo,
        max_resultados=max_resultados,
    )


__all__ = [
    "analisar_cesta_compras",
    "simular_promocao_cesta",
    "minerar_cestas_frequentes",
    "analyze_basket_logic",
    "simulate_promotion_logic",
    "mine_market_basket_logic",
]
