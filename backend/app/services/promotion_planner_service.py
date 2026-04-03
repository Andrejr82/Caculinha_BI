from __future__ import annotations

import logging
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence

from backend.app.core.data_scope_service import data_scope_service
from backend.app.core.duckdb_config import get_safe_connection
from backend.app.core.utils.query_router import (
    extract_days_param,
    extract_percentage_param,
    extract_segment_filter,
)
from backend.app.schemas.basket_analysis import BasketAnalysisRequest
from backend.app.services.basket_analysis_service import BasketAnalysisService

logger = logging.getLogger(__name__)


class PromotionPlannerService:
    """Planejador promocional determinístico para respostas operacionais no chat."""

    def __init__(self) -> None:
        self.basket_service = BasketAnalysisService()

    @staticmethod
    def should_plan(query: str) -> bool:
        q = str(query or "").strip().lower()
        if not q:
            return False
        planning_markers = [
            "como fazer",
            "como montar",
            "plano promocional",
            "plano de promocao",
            "estratégia promocional",
            "estrategia promocional",
            "acao promocional",
            "ação promocional",
            "campanha promocional",
            "como promover",
            "como executar",
        ]
        promo_markers = [
            "promo",
            "promoc",
            "desconto",
            "oferta",
            "campanha",
            "combo",
            "cross-sell",
            "cross sell",
            "combinam com",
        ]
        return any(marker in q for marker in planning_markers) and any(marker in q for marker in promo_markers)

    def build_plan(self, query: str, user: Any | None = None) -> Dict[str, Any]:
        params = self._extract_request_params(query)
        if not params["segment"] and not params["target_terms"] and params["discount_pct"] is None:
            return self._clarification_response()

        effective_user = self._coerce_user(user)
        product_stats = self._query_product_stats(params, user=effective_user)
        store_stats = self._query_store_stats(params, user=effective_user)
        basket_result = self.basket_service.analyze(
            BasketAnalysisRequest(
                segment=params["segment"],
                target_terms=params["target_terms"] or None,
                max_rules=8,
            ),
            user=effective_user,
        )

        mechanic = self._recommend_mechanic(product_stats, basket_result, params)
        response_text = self._format_plan_response(
            params=params,
            product_stats=product_stats,
            store_stats=store_stats,
            basket_result=basket_result,
            mechanic=mechanic,
        )

        table_data = self._build_table_data(product_stats, store_stats, basket_result, mechanic)
        return {
            "response": response_text,
            "result": {"mensagem": response_text},
            "table_data": table_data,
            "source": "service.promotion_planner",
            "mode": "promotion_planner",
            "confidence": 0.91 if product_stats else 0.78,
            "tool_calls": [
                {
                    "name": "promotion_planner_service",
                    "args": {
                        "segment": params["segment"],
                        "target_terms": params["target_terms"],
                        "discount_pct": params["discount_pct"],
                        "days": params["days"],
                    },
                }
            ],
        }

    @staticmethod
    def _clarification_response() -> Dict[str, Any]:
        msg = (
            "## Resumo executivo\n"
            "- Para montar um plano promocional real eu preciso do alvo principal da ação.\n\n"
            "## Plano promocional\n"
            "| Elemento | O que informar |\n"
            "|---|---|\n"
            "| Produto ou grupo | SKU, nome do item, segmento ou categoria |\n"
            "| Escopo | loja, UNE ou rede |\n"
            "| Janela | por quantos dias a ação deve rodar |\n\n"
            "## Próximas ações\n"
            "- Exemplo: 'como fazer uma promoção do EVA nas lojas 1685 e 2365 por 7 dias'."
        )
        return {
            "response": msg,
            "result": {"mensagem": msg},
            "source": "service.promotion_planner",
            "mode": "promotion_planner_clarification",
            "confidence": 0.82,
        }

    def _extract_request_params(self, query: str) -> Dict[str, Any]:
        target_terms = self._extract_target_terms(query)
        return {
            "segment": extract_segment_filter(query),
            "target_terms": target_terms,
            "discount_pct": extract_percentage_param(query),
            "days": extract_days_param(query) or 7,
            "query": query,
        }

    @staticmethod
    def _extract_target_terms(query: str) -> List[str]:
        q = str(query or "")
        patterns = [
            r"combinam\s+com\s+(.+?)(?:\s+em\s+uma?\s+a[çc][aã]o|\?|$)",
            r"promo[çc][aã]o\s+(?:de|do|da)\s+(.+?)(?:\s+nas?\s+|\s+por\s+|\?|$)",
            r"como\s+promover\s+(.+?)(?:\s+nas?\s+|\s+por\s+|\?|$)",
        ]
        chunk = None
        for pattern in patterns:
            match = re.search(pattern, q, re.IGNORECASE)
            if match:
                chunk = match.group(1)
                break
        if not chunk:
            return []
        normalized = re.sub(r"\s+e\s+", ",", chunk, flags=re.IGNORECASE)
        candidates = [part.strip(" .,:;!?-") for part in normalized.split(",")]
        blocked = {"produto", "produtos", "item", "itens", "acao promocional", "ação promocional"}
        terms: List[str] = []
        seen: set[str] = set()
        for item in candidates:
            if not item:
                continue
            folded = item.casefold()
            if folded in blocked or len(folded) < 2 or folded in seen:
                continue
            seen.add(folded)
            terms.append(item)
        return terms

    def _query_product_stats(self, params: Dict[str, Any], *, user: Any | None) -> List[Dict[str, Any]]:
        with get_safe_connection() as con:
            rel = data_scope_service.get_filtered_dataframe(self._coerce_user(user), conn=con)
            columns = set(rel.limit(0).columns)
            product_col = self._resolve_column(columns, "PRODUTO")
            name_col = self._resolve_column(columns, "NOME")
            segment_col = self._resolve_column(columns, "NOMESEGMENTO", "SEGMENTO")
            sales_col = self._resolve_column(columns, "VENDA_30DD")
            stock_col = self._resolve_column(columns, "ESTOQUE_UNE")
            price_col = self._resolve_column(columns, "LIQUIDO_38", "PRECO_VENDA")
            cost_col = self._resolve_column(columns, "ULTIMA_ENTRADA_CUSTO_CD", "PRECO_CUSTO")
            if not all([product_col, name_col, segment_col, sales_col, stock_col, price_col, cost_col]):
                return []
            query_filters = self._build_product_filter_sql(params, name_col=name_col, segment_col=segment_col)
            if not query_filters:
                return []
            sql = f"""
                SELECT
                    {product_col} AS produto,
                    {name_col} AS nome,
                    {segment_col} AS segmento,
                    SUM(COALESCE(TRY_CAST({sales_col} AS DOUBLE), 0)) AS venda_30dd,
                    SUM(COALESCE(TRY_CAST({stock_col} AS DOUBLE), 0)) AS estoque_total,
                    AVG(COALESCE(TRY_CAST({price_col} AS DOUBLE), 0)) AS preco_medio,
                    AVG(COALESCE(TRY_CAST({cost_col} AS DOUBLE), 0)) AS custo_medio
                FROM base
                WHERE {query_filters}
                GROUP BY 1, 2, 3
                ORDER BY venda_30dd DESC, estoque_total DESC
                LIMIT 8
            """
            return rel.query("base", sql).fetchdf().to_dict("records")

    def _query_store_stats(self, params: Dict[str, Any], *, user: Any | None) -> List[Dict[str, Any]]:
        with get_safe_connection() as con:
            rel = data_scope_service.get_filtered_dataframe(self._coerce_user(user), conn=con)
            columns = set(rel.limit(0).columns)
            une_col = self._resolve_column(columns, "UNE")
            name_col = self._resolve_column(columns, "NOME")
            segment_col = self._resolve_column(columns, "NOMESEGMENTO", "SEGMENTO")
            sales_col = self._resolve_column(columns, "VENDA_30DD")
            stock_col = self._resolve_column(columns, "ESTOQUE_UNE")
            price_col = self._resolve_column(columns, "LIQUIDO_38", "PRECO_VENDA")
            cost_col = self._resolve_column(columns, "ULTIMA_ENTRADA_CUSTO_CD", "PRECO_CUSTO")
            if not all([une_col, name_col, segment_col, sales_col, stock_col, price_col, cost_col]):
                return []
            query_filters = self._build_product_filter_sql(params, name_col=name_col, segment_col=segment_col)
            if not query_filters:
                return []
            sql = f"""
                SELECT
                    {une_col} AS une,
                    SUM(COALESCE(TRY_CAST({sales_col} AS DOUBLE), 0)) AS venda_30dd,
                    SUM(COALESCE(TRY_CAST({stock_col} AS DOUBLE), 0)) AS estoque_total,
                    AVG(COALESCE(TRY_CAST({price_col} AS DOUBLE), 0)) AS preco_medio,
                    AVG(COALESCE(TRY_CAST({cost_col} AS DOUBLE), 0)) AS custo_medio
                FROM base
                WHERE {query_filters}
                GROUP BY 1
                ORDER BY estoque_total DESC, venda_30dd ASC
                LIMIT 6
            """
            rows = rel.query("base", sql).fetchdf().to_dict("records")
            for row in rows:
                row["margem_pct"] = self._margin_pct(row.get("preco_medio"), row.get("custo_medio"))
                row["cobertura_dias"] = self._coverage_days(row.get("estoque_total"), row.get("venda_30dd"))
            return rows

    def _build_product_filter_sql(self, params: Dict[str, Any], *, name_col: str, segment_col: str) -> str:
        clauses: List[str] = []
        if params["segment"]:
            clauses.append(f"UPPER({segment_col}) = '{self._sql_escape(params['segment'].upper())}'")
        if params["target_terms"]:
            term_conditions = [
                f"UPPER({name_col}) LIKE '%{self._sql_escape(str(term).upper())}%'"
                for term in params["target_terms"]
            ]
            clauses.append("(" + " OR ".join(term_conditions) + ")")
        return " AND ".join(clauses) if clauses else ""

    def _recommend_mechanic(
        self,
        product_stats: List[Dict[str, Any]],
        basket_result: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        lead_product = product_stats[0] if product_stats else {}
        current_margin = self._margin_pct(lead_product.get("preco_medio"), lead_product.get("custo_medio"))
        cover_days = self._coverage_days(lead_product.get("estoque_total"), lead_product.get("venda_30dd"))
        requested_discount = params.get("discount_pct")
        top_rules = basket_result.get("top_rules") or []
        best_rule = top_rules[0] if top_rules else None

        recommended_discount = 0.0
        if requested_discount is not None:
            recommended_discount = float(requested_discount)
        elif current_margin is not None:
            if current_margin >= 35 and (cover_days or 0) >= 30:
                recommended_discount = 10.0
            elif current_margin >= 28 and (cover_days or 0) >= 21:
                recommended_discount = 8.0
            elif current_margin >= 20 and (cover_days or 0) >= 14:
                recommended_discount = 5.0
            else:
                recommended_discount = 0.0

        projected_margin = self._project_discounted_margin(current_margin, recommended_discount)
        combo_item = None
        if best_rule:
            combo_candidates = list(best_rule.get("consequent") or [])
            combo_item = combo_candidates[0] if combo_candidates else None

        if combo_item and (projected_margin is None or projected_margin < 15):
            strategy = "combo_ancora_sem_desconto_linear"
            recommended_discount = 0.0
            projected_margin = current_margin
        elif combo_item:
            strategy = "combo_ancora_com_desconto_controlado"
        else:
            strategy = "desconto_controlado"

        return {
            "strategy": strategy,
            "recommended_discount_pct": round(recommended_discount, 1),
            "current_margin_pct": current_margin,
            "projected_margin_pct": projected_margin,
            "cover_days": cover_days,
            "combo_item": combo_item,
            "best_rule": best_rule,
            "window_days": params["days"],
        }

    def _format_plan_response(
        self,
        *,
        params: Dict[str, Any],
        product_stats: List[Dict[str, Any]],
        store_stats: List[Dict[str, Any]],
        basket_result: Dict[str, Any],
        mechanic: Dict[str, Any],
    ) -> str:
        lead = product_stats[0] if product_stats else {}
        foco = lead.get("nome") or (params["segment"] and f"segmento {params['segment']}") or ", ".join(params["target_terms"])
        top_unes = [str(row.get("une")) for row in store_stats[:3] if row.get("une") not in (None, "", "nan")]
        unes_txt = ", ".join(top_unes) if top_unes else "rede com maior estoque disponível"
        strategy_map = {
            "combo_ancora_sem_desconto_linear": "Combo com item âncora, sem desconto linear agressivo",
            "combo_ancora_com_desconto_controlado": "Combo com item âncora e desconto controlado",
            "desconto_controlado": "Desconto controlado sobre o item foco",
        }
        strategy_txt = strategy_map.get(mechanic["strategy"], "Ação promocional controlada")
        current_margin = mechanic.get("current_margin_pct")
        projected_margin = mechanic.get("projected_margin_pct")
        rule = mechanic.get("best_rule") or {}
        combo_item = mechanic.get("combo_item")
        support = rule.get("support")
        confidence = rule.get("confidence")
        lift = rule.get("lift")
        kpi_rows = [
            ("Foco da ação", str(foco or "definir produto/segmento")),
            ("Janela recomendada", f"{mechanic['window_days']} dias"),
            ("Mecânica", strategy_txt),
            ("Desconto sugerido", f"{mechanic['recommended_discount_pct']:.1f}%"),
            ("Margem atual estimada", self._fmt_pct(current_margin)),
            ("Margem pós-oferta estimada", self._fmt_pct(projected_margin)),
            ("Lojas alvo", unes_txt),
        ]
        if combo_item:
            kpi_rows.append(("Item complementar", str(combo_item)))

        plan_table = "\n".join([f"| {k} | {v} |" for k, v in kpi_rows])
        store_table = self._markdown_table(
            [
                {
                    "UNE": row.get("une"),
                    "Venda 30d": self._fmt_num(row.get("venda_30dd")),
                    "Estoque": self._fmt_num(row.get("estoque_total"), digits=0),
                    "Cobertura (dias)": self._fmt_num(row.get("cobertura_dias"), digits=0),
                    "Margem (%)": self._fmt_pct(row.get("margem_pct")),
                }
                for row in store_stats[:5]
            ]
        )

        execution_lines = [
            f"- Monte a ação por {mechanic['window_days']} dias, priorizando {unes_txt}.",
            f"- Use {strategy_txt.lower()} como mecânica principal.",
        ]
        if combo_item:
            execution_lines.append(
                f"- Faça exposição conjunta de {foco} com {combo_item} e mensagem comercial de solução completa."
            )
        if support is not None and confidence is not None and lift is not None:
            execution_lines.append(
                f"- Regra de cesta que sustenta o combo: support {support:.2%}, confidence {confidence:.2%}, lift {lift:.2f}."
            )
        execution_lines.extend(
            [
                "- Ative preço/etiqueta e comunicação apenas nas lojas com cobertura suficiente, evitando empurrar SKU em ruptura.",
                "- Revise D+1 e D+3 para ajustar desconto, exposição e reposição.",
            ]
        )

        control_lines = [
            f"- Meta mínima de margem pós-oferta: 15%. Hoje a projeção está em {self._fmt_pct(projected_margin)}.",
            "- Pausar a ação se a cobertura projetada cair abaixo de 7 dias sem reposição confirmada.",
            "- Medir sell-out incremental, ticket médio e adesão ao combo por loja.",
        ]

        return (
            "## Resumo executivo\n"
            f"- A melhor forma de promover {foco} hoje é: {strategy_txt}.\n"
            f"- Desconto sugerido: {mechanic['recommended_discount_pct']:.1f}% com janela de {mechanic['window_days']} dias.\n"
            f"- Priorizar execução em: {unes_txt}.\n\n"
            "## Plano promocional\n"
            "| Elemento | Recomendação |\n"
            "|---|---|\n"
            f"{plan_table}\n\n"
            "## Tabela operacional\n"
            f"{store_table}\n\n"
            "## Como executar\n"
            + "\n".join(execution_lines)
            + "\n\n## KPI e gatilhos\n"
            + "\n".join(control_lines)
        )

    @staticmethod
    def _build_table_data(
        product_stats: List[Dict[str, Any]],
        store_stats: List[Dict[str, Any]],
        basket_result: Dict[str, Any],
        mechanic: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for row in store_stats[:5]:
            rows.append(
                {
                    "tipo": "loja_alvo",
                    "une": row.get("une"),
                    "venda_30dd": row.get("venda_30dd"),
                    "estoque_total": row.get("estoque_total"),
                    "cobertura_dias": row.get("cobertura_dias"),
                    "margem_pct": row.get("margem_pct"),
                }
            )
        for rule in (basket_result.get("top_rules") or [])[:3]:
            rows.append(
                {
                    "tipo": "cross_sell",
                    "antecedent": " + ".join(rule.get("antecedent") or []),
                    "consequent": " + ".join(rule.get("consequent") or []),
                    "support": rule.get("support"),
                    "confidence": rule.get("confidence"),
                    "lift": rule.get("lift"),
                }
            )
        if product_stats:
            lead = product_stats[0]
            rows.insert(
                0,
                {
                    "tipo": "foco",
                    "produto": lead.get("produto"),
                    "nome": lead.get("nome"),
                    "segmento": lead.get("segmento"),
                    "venda_30dd": lead.get("venda_30dd"),
                    "estoque_total": lead.get("estoque_total"),
                    "desconto_sugerido_pct": mechanic.get("recommended_discount_pct"),
                },
            )
        return rows

    @staticmethod
    def _coerce_user(user: Any | None) -> Any:
        if user is not None and hasattr(user, "role") and hasattr(user, "segments_list"):
            return user
        return SimpleNamespace(role="admin", username="promotion-planner", segments_list=["*"])

    @staticmethod
    def _resolve_column(columns: Sequence[str], *candidates: str) -> Optional[str]:
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    @staticmethod
    def _sql_escape(value: str) -> str:
        return str(value).replace("'", "''")

    @staticmethod
    def _margin_pct(price: Any, cost: Any) -> Optional[float]:
        try:
            p = float(price or 0)
            c = float(cost or 0)
            if p <= 0:
                return None
            return round(((p - c) / p) * 100.0, 2)
        except Exception:
            return None

    @staticmethod
    def _project_discounted_margin(current_margin_pct: Any, discount_pct: Any) -> Optional[float]:
        try:
            if current_margin_pct is None:
                return None
            current_margin_ratio = float(current_margin_pct) / 100.0
            cost_ratio = 1.0 - current_margin_ratio
            new_price_ratio = 1.0 - (float(discount_pct or 0) / 100.0)
            if new_price_ratio <= 0:
                return None
            new_margin_ratio = (new_price_ratio - cost_ratio) / new_price_ratio
            return round(new_margin_ratio * 100.0, 2)
        except Exception:
            return None

    @staticmethod
    def _coverage_days(stock_total: Any, venda_30dd: Any) -> Optional[float]:
        try:
            stock = float(stock_total or 0)
            sales = float(venda_30dd or 0)
            if stock <= 0 or sales <= 0:
                return None
            daily = sales / 30.0
            if daily <= 0:
                return None
            return round(stock / daily, 1)
        except Exception:
            return None

    @staticmethod
    def _fmt_num(value: Any, digits: int = 2) -> str:
        if value in (None, ""):
            return "-"
        try:
            number = float(value)
            return f"{number:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return str(value)

    @staticmethod
    def _fmt_pct(value: Any) -> str:
        if value is None:
            return "-"
        try:
            return f"{float(value):.1f}%".replace(".", ",")
        except Exception:
            return str(value)

    @staticmethod
    def _markdown_table(rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "Sem dados operacionais suficientes para listar lojas alvo."
        headers = list(rows[0].keys())
        head = "| " + " | ".join(headers) + " |\n|---" * len(headers) + "|"
        body = [
            "| " + " | ".join(str(row.get(header, "-")) for header in headers) + " |"
            for row in rows
        ]
        return head + "\n" + "\n".join(body)
