from __future__ import annotations

import logging
import math
import os
import re
import unicodedata
from itertools import combinations
from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from typing import Any

import pandas as pd

from backend.app.config.settings import settings
from backend.app.core.context import get_current_user_context
from backend.app.core.data_scope_service import data_scope_service
from backend.app.core.duckdb_config import get_safe_connection

logger = logging.getLogger(__name__)

try:
    from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth

    MLXTEND_AVAILABLE = True
except ImportError:  # pragma: no cover - dependency guard
    apriori = None
    association_rules = None
    fpgrowth = None
    MLXTEND_AVAILABLE = False


ROLE_LABELS: dict[str, str] = {
    "transaction_key": "transaction key",
    "product_key": "product key",
    "product_name": "product name",
    "date_key": "date key",
    "une": "une",
    "segment": "segment",
    "category": "category",
    "customer": "customer",
}

ROLE_ALIASES: dict[str, tuple[str, ...]] = {
    "transaction_key": (
        "transactionid",
        "transactionkey",
        "ticketid",
        "pedidoid",
        "vendaid",
        "cupom",
        "ordem",
        "orderid",
        "saleid",
        "basketid",
        "nota",
        "notafiscal",
    ),
    "product_key": (
        "productid",
        "produto",
        "produtoid",
        "sku",
        "codigo",
        "codproduto",
        "itemid",
        "ean",
    ),
    "product_name": (
        "nome",
        "descricao",
        "description",
        "produtonome",
    ),
    "date_key": (
        "datavenda",
        "transactiondate",
        "venda_data",
        "sale_date",
        "notaemissao",
        "data",
        "ultimavendadataune",
    ),
    "une": ("une", "loja", "lojaid"),
    "segment": ("nomesegmento", "segmento"),
    "category": ("nomecategoria", "categoria", "grupo", "nomegrupo"),
    "customer": ("cliente", "customerid", "customer", "clientid"),
}

STRONG_TRANSACTION_ALIASES = {
    "transactionid",
    "transactionkey",
    "ticketid",
    "pedidoid",
    "vendaid",
    "cupom",
    "orderid",
    "saleid",
    "basketid",
}
HYPOTHESIS_TRANSACTION_ALIASES = {"nota", "notafiscal"}


class BasketAnalysisService:
    """Serviço analítico para market basket sobre a base local."""

    MIN_REAL_COVERAGE_RATIO = 0.05
    MIN_REAL_TRANSACTIONS = 100
    MIN_REAL_MULTI_ITEM_TRANSACTIONS = 30
    MIN_REAL_MULTI_ITEM_RATIO = 0.25

    MIN_SUBSET_COVERAGE_RATIO = 0.01
    MIN_SUBSET_TRANSACTIONS = 300
    MIN_SUBSET_MULTI_ITEM_TRANSACTIONS = 150
    MIN_SUBSET_MULTI_ITEM_RATIO = 0.50
    MIN_SUBSET_THREE_PLUS_RATIO = 0.40

    def analyze(self, request: Any, user: Any | None = None) -> dict[str, Any]:
        params = self._normalize_request(request)
        base_frame, available_columns = self._load_source_frame(user=user)
        schema = self.detect_transaction_schema(available_columns)
        diagnostics: dict[str, Any] = {
            "available_columns_count": len(available_columns),
            "detected_columns": schema,
        }

        validation = self.validate_transaction_support(base_frame, schema)
        diagnostics["support"] = validation

        if validation["analysis_mode"] == "unsupported":
            limitations = self.build_limitations(validation, params=params)
            return self._build_response(
                status="unsupported",
                analysis_mode="unsupported",
                parameters=params,
                diagnostics=diagnostics,
                limitations=limitations,
            )

        transaction_frame = self.build_transaction_frame(base_frame, schema, params)
        if transaction_frame.empty:
            limitations = self.build_limitations(validation, params=params, transaction_frame=transaction_frame)
            return self._build_response(
                status="no_data",
                analysis_mode=validation["analysis_mode"],
                parameters=params,
                diagnostics=diagnostics,
                limitations=limitations,
            )

        basket_matrix = self.build_basket_matrix(transaction_frame)
        diagnostics["basket_matrix"] = {
            "transactions": int(basket_matrix.shape[0]),
            "items": int(basket_matrix.shape[1]),
        }
        if basket_matrix.empty:
            limitations = self.build_limitations(validation, params=params, transaction_frame=transaction_frame)
            return self._build_response(
                status="no_data",
                analysis_mode=validation["analysis_mode"],
                parameters=params,
                diagnostics=diagnostics,
                limitations=limitations,
            )

        itemsets_df, algorithm = self.run_frequent_itemsets(
            basket_matrix,
            min_support=params["min_support"],
        )
        rules_df = self.run_association_rules(
            itemsets_df,
            min_confidence=params["min_confidence"],
            min_lift=params["min_lift"],
            max_rules=params["max_rules"],
        )

        if params["target_product"]:
            rules_df = self._filter_rules_for_target(rules_df, params["target_product"])
            itemsets_df = self._filter_itemsets_for_target(itemsets_df, params["target_product"])
        if params["target_terms"]:
            rules_df = self._filter_rules_for_terms(rules_df, params["target_terms"])
            itemsets_df = self._filter_itemsets_for_terms(itemsets_df, params["target_terms"])

        top_itemsets = self._serialize_itemsets(itemsets_df, params["max_rules"])
        top_rules = self._serialize_rules(rules_df, params["max_rules"])
        limitations = self.build_limitations(
            validation,
            params=params,
            transaction_frame=transaction_frame,
            top_rules=top_rules,
        )
        summary = self.build_business_summary(
            validation=validation,
            top_rules=top_rules,
            top_itemsets=top_itemsets,
            transactions_analyzed=int(transaction_frame["transaction_key"].nunique()),
            target_product=params["target_product"],
            target_terms=params["target_terms"],
        )
        diagnostics["algorithm"] = algorithm

        return self._build_response(
            status="success",
            analysis_mode=validation["analysis_mode"],
            parameters=params,
            diagnostics=diagnostics,
            limitations=limitations,
            transactions_analyzed=int(transaction_frame["transaction_key"].nunique()),
            unique_items=int(transaction_frame["product_key"].nunique()),
            top_itemsets=top_itemsets,
            top_rules=top_rules,
            business_summary=summary,
        )

    def detect_transaction_schema(self, columns: Sequence[str]) -> dict[str, Any]:
        normalized_lookup = {self._normalize_column_name(column): str(column) for column in columns}
        candidates: dict[str, list[str]] = {}
        selected: dict[str, str | None] = {}

        for role, aliases in ROLE_ALIASES.items():
            matched = [normalized_lookup[alias] for alias in aliases if alias in normalized_lookup]
            candidates[role] = matched
            selected[role] = matched[0] if matched else None

        transaction_alias = self._normalize_column_name(selected["transaction_key"])
        if transaction_alias in STRONG_TRANSACTION_ALIASES:
            confidence = "strong"
        elif transaction_alias in HYPOTHESIS_TRANSACTION_ALIASES:
            confidence = "hypothesis"
        else:
            confidence = "none"

        return {
            "candidate_columns": candidates,
            "selected_columns": selected,
            "transaction_key_confidence": confidence,
        }

    def validate_transaction_support(self, frame: pd.DataFrame, schema: Mapping[str, Any]) -> dict[str, Any]:
        selected = schema.get("selected_columns", {})
        transaction_col = selected.get("transaction_key")
        product_col = selected.get("product_key")
        date_col = selected.get("date_key")
        une_col = selected.get("une")
        reasons: list[str] = []

        if not transaction_col:
            reasons.append("Nenhuma coluna candidata de transaction key foi detectada.")
        if not product_col:
            reasons.append("Nenhuma coluna candidata de product key foi detectada.")
        if reasons:
            return {
                "analysis_mode": "unsupported",
                "transaction_column": transaction_col,
                "product_column": product_col,
                "reasons": reasons,
                "metrics": {},
            }

        support_columns = [transaction_col, product_col]
        for optional_column in (
            date_col,
            une_col,
            "TIPO" if "TIPO" in frame.columns else None,
            "SERIE" if "SERIE" in frame.columns else None,
            "PICKLIST" if "PICKLIST" in frame.columns else None,
            "ROMANEIO_SOLICITACAO" if "ROMANEIO_SOLICITACAO" in frame.columns else None,
            "ROMANEIO_ENVIO" if "ROMANEIO_ENVIO" in frame.columns else None,
            "SOLICITACAO_PENDENTE" if "SOLICITACAO_PENDENTE" in frame.columns else None,
        ):
            if optional_column and optional_column not in support_columns:
                support_columns.append(optional_column)

        working = frame[support_columns].copy()
        working[transaction_col] = working[transaction_col].apply(self._clean_key)
        working[product_col] = working[product_col].apply(self._clean_key)
        rows_total = int(len(working))
        rows_with_transaction = int(working[transaction_col].notna().sum())
        valid_rows = working[
            working[transaction_col].notna() & working[product_col].notna()
        ].copy()
        if date_col and date_col in valid_rows.columns:
            valid_rows[date_col] = pd.to_datetime(valid_rows[date_col], errors="coerce")
        rows_with_both = int(len(valid_rows))
        transactions_analyzed = int(valid_rows[transaction_col].nunique())
        unique_items = int(valid_rows[product_col].nunique())

        if rows_with_both == 0 or transactions_analyzed == 0:
            reasons.append("Nao ha linhas suficientes com transaction key e product key preenchidas.")
            return {
                "analysis_mode": "unsupported",
                "transaction_column": transaction_col,
                "product_column": product_col,
                "reasons": reasons,
                "metrics": {
                    "rows_total": rows_total,
                    "rows_with_transaction_key": rows_with_transaction,
                    "rows_with_transaction_and_product": rows_with_both,
                    "distinct_transactions": transactions_analyzed,
                    "distinct_products": unique_items,
                },
            }

        counts = valid_rows.groupby(transaction_col)[product_col].nunique()
        multi_item_transactions = int((counts >= 2).sum())
        three_plus_transactions = int((counts >= 3).sum())
        avg_items = float(counts.mean()) if not counts.empty else 0.0
        median_items = float(counts.median()) if not counts.empty else 0.0
        pct_single_item = float((counts == 1).mean()) if not counts.empty else 0.0
        pct_two_plus = float((counts >= 2).mean()) if not counts.empty else 0.0
        pct_three_plus = float((counts >= 3).mean()) if not counts.empty else 0.0
        coverage_ratio = rows_with_transaction / rows_total if rows_total else 0.0
        multi_item_ratio = (
            multi_item_transactions / transactions_analyzed if transactions_analyzed else 0.0
        )
        confidence = str(schema.get("transaction_key_confidence") or "none")

        consistency_frame = valid_rows.copy()
        duplicate_note_product = int(
            consistency_frame.duplicated(subset=[transaction_col, product_col]).sum()
        )
        transactions_multiple_unes = 0
        if une_col and une_col in consistency_frame.columns:
            transactions_multiple_unes = int(
                (consistency_frame.groupby(transaction_col)[une_col].nunique() > 1).sum()
            )
        transactions_multiple_dates = 0
        period_coverage_by_day: list[dict[str, Any]] = []
        period_coverage_by_month: list[dict[str, Any]] = []
        months_covered = 0
        days_covered = 0
        if date_col and date_col in consistency_frame.columns:
            dates = consistency_frame[date_col]
            transactions_multiple_dates = int(
                (consistency_frame.groupby(transaction_col)[date_col].nunique(dropna=True) > 1).sum()
            )
            daily = (
                consistency_frame.dropna(subset=[date_col])
                .assign(_day=consistency_frame[date_col].dt.date)
                .groupby("_day")
                .agg(
                    lines_with_transaction=(transaction_col, "count"),
                    distinct_transactions=(transaction_col, "nunique"),
                    distinct_unes=(une_col, "nunique") if une_col and une_col in consistency_frame.columns else (transaction_col, "nunique"),
                )
                .reset_index()
                .sort_values("_day")
            )
            period_coverage_by_day = [
                {
                    "date": str(row["_day"]),
                    "lines_with_transaction": int(row["lines_with_transaction"]),
                    "distinct_transactions": int(row["distinct_transactions"]),
                    "distinct_unes": int(row["distinct_unes"]),
                }
                for _, row in daily.iterrows()
            ]
            monthly = (
                consistency_frame.dropna(subset=[date_col])
                .assign(_month=consistency_frame[date_col].dt.strftime("%Y-%m"))
                .groupby("_month")
                .agg(
                    lines_with_transaction=(transaction_col, "count"),
                    distinct_transactions=(transaction_col, "nunique"),
                    distinct_unes=(une_col, "nunique") if une_col and une_col in consistency_frame.columns else (transaction_col, "nunique"),
                )
                .reset_index()
                .sort_values("_month")
            )
            period_coverage_by_month = [
                {
                    "month": str(row["_month"]),
                    "lines_with_transaction": int(row["lines_with_transaction"]),
                    "distinct_transactions": int(row["distinct_transactions"]),
                    "distinct_unes": int(row["distinct_unes"]),
                }
                for _, row in monthly.iterrows()
            ]
            days_covered = len(period_coverage_by_day)
            months_covered = len(period_coverage_by_month)

        coverage_by_une: list[dict[str, Any]] = []
        if une_col and une_col in working.columns:
            une_totals = (
                working.groupby(une_col)
                .agg(
                    total_rows=(transaction_col, "size"),
                    rows_with_transaction_key=(transaction_col, lambda s: int(s.notna().sum())),
                    distinct_transactions=(transaction_col, lambda s: int(s.dropna().nunique())),
                )
                .reset_index()
            )
            coverage_by_une = [
                {
                    "une": str(row[une_col]),
                    "total_rows": int(row["total_rows"]),
                    "rows_with_transaction_key": int(row["rows_with_transaction_key"]),
                    "coverage_pct": round(
                        (float(row["rows_with_transaction_key"]) / float(row["total_rows"]) * 100.0)
                        if row["total_rows"]
                        else 0.0,
                        4,
                    ),
                    "distinct_transactions": int(row["distinct_transactions"]),
                }
                for _, row in une_totals.sort_values(
                    ["rows_with_transaction_key", "total_rows"],
                    ascending=[False, False],
                ).iterrows()
            ]

        logistics_signal_ratios: dict[str, float] = {}
        for signal_column in ("PICKLIST", "ROMANEIO_SOLICITACAO", "ROMANEIO_ENVIO", "SOLICITACAO_PENDENTE"):
            if signal_column not in valid_rows.columns:
                continue
            numeric_signal = pd.to_numeric(valid_rows[signal_column], errors="coerce")
            non_null = numeric_signal.notna()
            active = non_null & (numeric_signal != 0)
            logistics_signal_ratios[signal_column] = round(float(active.mean()) if len(valid_rows) else 0.0, 4)

        transaction_column_is_nota = self._normalize_column_name(transaction_col) in HYPOTHESIS_TRANSACTION_ALIASES
        semantic_signals = {
            "transaction_column_is_nota": transaction_column_is_nota,
            "single_une_per_transaction": transactions_multiple_unes == 0,
            "single_date_per_transaction": transactions_multiple_dates == 0,
            "duplicate_note_product_rows": duplicate_note_product == 0,
            "logistics_coupling_detected": any(value >= 0.5 for value in logistics_signal_ratios.values()),
        }

        metrics = {
            "rows_total": rows_total,
            "rows_with_transaction_key": rows_with_transaction,
            "rows_with_transaction_and_product": rows_with_both,
            "distinct_transactions": transactions_analyzed,
            "distinct_products": unique_items,
            "multi_item_transactions": multi_item_transactions,
            "three_plus_item_transactions": three_plus_transactions,
            "coverage_ratio": round(coverage_ratio, 4),
            "multi_item_ratio": round(multi_item_ratio, 4),
            "avg_items_per_transaction": round(avg_items, 4),
            "median_items_per_transaction": round(median_items, 4),
            "pct_transactions_single_item": round(pct_single_item, 4),
            "pct_transactions_two_plus_items": round(pct_two_plus, 4),
            "pct_transactions_three_plus_items": round(pct_three_plus, 4),
            "transactions_multiple_unes": transactions_multiple_unes,
            "transactions_multiple_dates": transactions_multiple_dates,
            "duplicate_transaction_product_rows": duplicate_note_product,
            "days_covered": days_covered,
            "months_covered": months_covered,
            "coverage_by_une": coverage_by_une,
            "coverage_by_day": period_coverage_by_day,
            "coverage_by_month": period_coverage_by_month,
            "logistics_signal_ratios": logistics_signal_ratios,
            "semantic_signals": semantic_signals,
        }

        if (
            confidence == "strong"
            and coverage_ratio >= self.MIN_REAL_COVERAGE_RATIO
            and transactions_analyzed >= self.MIN_REAL_TRANSACTIONS
            and multi_item_transactions >= self.MIN_REAL_MULTI_ITEM_TRANSACTIONS
            and multi_item_ratio >= self.MIN_REAL_MULTI_ITEM_RATIO
            and not semantic_signals["logistics_coupling_detected"]
        ):
            mode = "real_transactional"
        elif (
            confidence == "hypothesis"
            and coverage_ratio >= self.MIN_SUBSET_COVERAGE_RATIO
            and transactions_analyzed >= self.MIN_SUBSET_TRANSACTIONS
            and multi_item_transactions >= self.MIN_SUBSET_MULTI_ITEM_TRANSACTIONS
            and multi_item_ratio >= self.MIN_SUBSET_MULTI_ITEM_RATIO
            and pct_three_plus >= self.MIN_SUBSET_THREE_PLUS_RATIO
            and transactions_multiple_unes == 0
            and transactions_multiple_dates == 0
            and duplicate_note_product == 0
        ):
            mode = "subset_transactional_supported"
            reasons.append(
                "A coluna transacional detectada sustenta apenas um subset controlado; ela nao representa a base principal inteira."
            )
            if semantic_signals["logistics_coupling_detected"]:
                reasons.append(
                    "Os sinais de picklist/romaneio indicam documentos fiscais-logisticos, nao uma cesta global de compra do cliente."
                )
        else:
            mode = "unsupported"
            if confidence == "hypothesis":
                reasons.append(
                    "A coluna transacional detectada e uma hipotese controlada e nao foi promovida para basket real."
                )
            reasons.append(
                "A cobertura transacional e insuficiente para habilitar analise de cesta confiavel na base local."
            )

        return {
            "analysis_mode": mode,
            "transaction_column": transaction_col,
            "product_column": product_col,
            "date_column": date_col,
            "une_column": une_col,
            "reasons": reasons,
            "metrics": metrics,
        }

    def build_transaction_frame(
        self,
        frame: pd.DataFrame,
        schema: Mapping[str, Any],
        params: Mapping[str, Any],
    ) -> pd.DataFrame:
        selected = schema.get("selected_columns", {})
        column_map = {
            "transaction_key": selected.get("transaction_key"),
            "product_key": selected.get("product_key"),
            "product_name": selected.get("product_name"),
            "transaction_date": selected.get("date_key"),
            "une": selected.get("une"),
            "segment": selected.get("segment"),
            "category": selected.get("category"),
        }
        present = {alias: source for alias, source in column_map.items() if source and source in frame.columns}
        if "transaction_key" not in present or "product_key" not in present:
            return pd.DataFrame(columns=list(column_map))

        working = frame[list(present.values())].rename(columns={source: alias for alias, source in present.items()})
        working["transaction_key"] = working["transaction_key"].apply(self._clean_key)
        working["product_key"] = working["product_key"].apply(self._clean_key)
        if "product_name" in working.columns:
            working["product_name"] = working["product_name"].fillna("").astype(str).str.strip()
        if "transaction_date" in working.columns:
            working["transaction_date"] = pd.to_datetime(working["transaction_date"], errors="coerce")
        for text_column in ("une", "segment", "category"):
            if text_column in working.columns:
                working[text_column] = working[text_column].astype(str).str.strip()

        working = working[
            working["transaction_key"].notna() & working["product_key"].notna()
        ].drop_duplicates(subset=["transaction_key", "product_key"])

        start_date = params.get("start_date")
        end_date = params.get("end_date")
        if start_date and "transaction_date" in working.columns:
            working = working[working["transaction_date"] >= pd.Timestamp(datetime.combine(start_date, time.min))]
        if end_date and "transaction_date" in working.columns:
            working = working[working["transaction_date"] <= pd.Timestamp(datetime.combine(end_date, time.max))]

        if params.get("une") and "une" in working.columns:
            working = working[working["une"].str.casefold() == str(params["une"]).strip().casefold()]
        if params.get("segment") and "segment" in working.columns:
            working = working[working["segment"].str.casefold() == str(params["segment"]).strip().casefold()]
        if params.get("category") and "category" in working.columns:
            working = working[working["category"].str.casefold() == str(params["category"]).strip().casefold()]

        return working.reset_index(drop=True)

    def build_basket_matrix(self, transaction_frame: pd.DataFrame) -> pd.DataFrame:
        if transaction_frame.empty:
            return pd.DataFrame()
        basket = pd.crosstab(transaction_frame["transaction_key"], transaction_frame["product_key"])
        return basket.gt(0)

    def run_frequent_itemsets(
        self,
        basket_matrix: pd.DataFrame,
        min_support: float,
    ) -> tuple[pd.DataFrame, str]:
        if basket_matrix.empty:
            return pd.DataFrame(columns=["support", "itemsets"]), "no_data"
        if not MLXTEND_AVAILABLE:
            return self._run_manual_frequent_itemsets(basket_matrix, min_support), "manual_pairs"

        working = basket_matrix.astype(bool)
        try:
            if fpgrowth is not None:
                itemsets = fpgrowth(working, min_support=min_support, use_colnames=True)
                if not itemsets.empty:
                    return itemsets, "fpgrowth"
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("fpgrowth failed, falling back to apriori: %s", exc)

        if apriori is None:
            return pd.DataFrame(columns=["support", "itemsets"]), "no_algorithm"
        itemsets = apriori(working, min_support=min_support, use_colnames=True)
        return itemsets, "apriori"

    def run_association_rules(
        self,
        itemsets: pd.DataFrame,
        min_confidence: float,
        min_lift: float,
        max_rules: int,
    ) -> pd.DataFrame:
        if itemsets.empty:
            return pd.DataFrame()
        if association_rules is None:
            return self._run_manual_association_rules(itemsets, min_confidence, min_lift, max_rules)
        frequent_itemsets = itemsets[itemsets["itemsets"].apply(lambda items: len(items) >= 2)].copy()
        if frequent_itemsets.empty:
            return pd.DataFrame()

        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        if rules.empty:
            return rules

        rules = rules[rules["lift"] >= min_lift].copy()
        if rules.empty:
            return rules

        rules.sort_values(["lift", "confidence", "support"], ascending=False, inplace=True)
        return rules.head(max_rules).reset_index(drop=True)

    @staticmethod
    def _run_manual_frequent_itemsets(
        basket_matrix: pd.DataFrame,
        min_support: float,
    ) -> pd.DataFrame:
        if basket_matrix.empty:
            return pd.DataFrame(columns=["support", "itemsets"])

        rows: list[dict[str, Any]] = []
        columns = list(basket_matrix.columns)
        for item in columns:
            support = float(basket_matrix[item].mean())
            if support >= min_support:
                rows.append(
                    {
                        "support": round(support, 4),
                        "itemsets": frozenset([str(item)]),
                    }
                )

        for left, right in combinations(columns, 2):
            support = float((basket_matrix[left] & basket_matrix[right]).mean())
            if support >= min_support:
                rows.append(
                    {
                        "support": round(support, 4),
                        "itemsets": frozenset([str(left), str(right)]),
                    }
                )

        if not rows:
            return pd.DataFrame(columns=["support", "itemsets"])

        return pd.DataFrame(rows).sort_values(["support"], ascending=False).reset_index(drop=True)

    @staticmethod
    def _run_manual_association_rules(
        itemsets: pd.DataFrame,
        min_confidence: float,
        min_lift: float,
        max_rules: int,
    ) -> pd.DataFrame:
        support_lookup = {
            frozenset(str(item) for item in row["itemsets"]): float(row["support"])
            for _, row in itemsets.iterrows()
        }
        rows: list[dict[str, Any]] = []

        for itemset, pair_support in support_lookup.items():
            if len(itemset) != 2:
                continue
            left, right = sorted(itemset)
            support_left = support_lookup.get(frozenset([left]), 0.0)
            support_right = support_lookup.get(frozenset([right]), 0.0)

            if support_left > 0:
                confidence = pair_support / support_left
                lift = confidence / support_right if support_right > 0 else 0.0
                if confidence >= min_confidence and lift >= min_lift:
                    rows.append(
                        {
                            "antecedents": frozenset([left]),
                            "consequents": frozenset([right]),
                            "support": pair_support,
                            "confidence": confidence,
                            "lift": lift,
                        }
                    )

            if support_right > 0:
                confidence = pair_support / support_right
                lift = confidence / support_left if support_left > 0 else 0.0
                if confidence >= min_confidence and lift >= min_lift:
                    rows.append(
                        {
                            "antecedents": frozenset([right]),
                            "consequents": frozenset([left]),
                            "support": pair_support,
                            "confidence": confidence,
                            "lift": lift,
                        }
                    )

        if not rows:
            return pd.DataFrame()

        return (
            pd.DataFrame(rows)
            .sort_values(["lift", "confidence", "support"], ascending=False)
            .head(max_rules)
            .reset_index(drop=True)
        )

    def build_business_summary(
        self,
        *,
        validation: Mapping[str, Any],
        top_rules: list[dict[str, Any]],
        top_itemsets: list[dict[str, Any]],
        transactions_analyzed: int,
        target_product: str | None,
        target_terms: Sequence[str] | None = None,
    ) -> list[str]:
        mode = validation.get("analysis_mode", "unsupported")
        if mode == "unsupported":
            return [
                "A base local nao comprovou granularidade transacional suficiente para market basket confiavel."
            ]

        summary: list[str] = []
        if mode == "subset_transactional_supported":
            summary.append(
                "Os achados abaixo sao inferencias analiticas sobre um subset controlado, nao uma verdade global da base principal."
            )

        if top_rules:
            best_rule = top_rules[0]
            antecedent = " + ".join(best_rule["antecedent"])
            consequent = " + ".join(best_rule["consequent"])
            summary.append(
                f"A associacao mais forte sugere {antecedent} -> {consequent} com lift {best_rule['lift']:.2f} e confidence {best_rule['confidence']:.2%}."
            )
            if target_product:
                summary.append(
                    f"O recorte priorizou regras relacionadas ao item alvo '{target_product}'."
                )
            elif target_terms:
                summary.append(
                    f"O recorte priorizou regras relacionadas aos termos-alvo: {', '.join(target_terms)}."
                )
        elif top_itemsets:
            first_itemset = top_itemsets[0]
            summary.append(
                f"O itemset mais frequente no recorte foi {' + '.join(first_itemset['items'])} com support {first_itemset['support']:.2%}."
            )
        else:
            summary.append(
                "O recorte teve transacoes validas, mas nao atingiu os thresholds atuais de support/confidence/lift."
            )

        summary.append(f"Foram analisadas {transactions_analyzed} transacoes distintas no recorte.")
        return summary

    def build_limitations(
        self,
        validation: Mapping[str, Any],
        *,
        params: Mapping[str, Any],
        transaction_frame: pd.DataFrame | None = None,
        top_rules: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        limitations = list(validation.get("reasons") or [])
        mode = validation.get("analysis_mode")
        confidence_note = validation.get("transaction_column")

        if mode in {"subset_transactional_supported", "unsupported"}:
            limitations.append(
                "A fonte principal do projeto e um snapshot analitico; market basket so pode subir de nivel com comprovacao transacional real."
            )
        if confidence_note and str(confidence_note).upper() == "NOTA":
            limitations.append(
                "A coluna NOTA e tratada como hipotese controlada, nao como verdade global de cesta de compra."
            )
        if params.get("start_date") or params.get("end_date"):
            selected_date = (
                validation.get("date_column")
                or validation.get("metrics", {}).get("date_column")
            )
            if not selected_date and transaction_frame is not None and "transaction_date" not in transaction_frame.columns:
                limitations.append("O filtro de periodo foi solicitado, mas nao ha date key confiavel no recorte.")
        if transaction_frame is not None and transaction_frame.empty:
            limitations.append("Os filtros aplicados nao retornaram transacoes suficientes para analise.")
        if top_rules is not None and not top_rules and mode != "unsupported":
            limitations.append("Nenhuma regra atingiu simultaneamente os thresholds de support, confidence e lift.")

        return list(dict.fromkeys(limitations))

    def _build_response(
        self,
        *,
        status: str,
        analysis_mode: str,
        parameters: Mapping[str, Any],
        diagnostics: Mapping[str, Any],
        limitations: list[str],
        transactions_analyzed: int = 0,
        unique_items: int = 0,
        top_itemsets: list[dict[str, Any]] | None = None,
        top_rules: list[dict[str, Any]] | None = None,
        business_summary: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "analysis_mode": analysis_mode,
            "data_source": settings.PARQUET_DATA_PATH,
            "transactions_analyzed": int(transactions_analyzed),
            "unique_items": int(unique_items),
            "parameters": dict(parameters),
            "top_itemsets": top_itemsets or [],
            "top_rules": top_rules or [],
            "business_summary": business_summary or [],
            "limitations": limitations,
            "diagnostics": dict(diagnostics),
        }

    def _load_source_frame(self, user: Any | None = None) -> tuple[pd.DataFrame, list[str]]:
        effective_user = user or get_current_user_context()
        if effective_user is None:
            raise ValueError("Nenhum contexto de usuario disponivel para carregar a base.")

        basket_csv_path = str(getattr(settings, "BASKET_TRANSACTIONS_CSV_PATH", "") or "").strip()
        if basket_csv_path and os.path.exists(basket_csv_path):
            frame = pd.read_csv(basket_csv_path)
            allowed_unes = None
            if isinstance(effective_user, Mapping):
                allowed_unes = effective_user.get("allowed_unes") or effective_user.get("unes")
            else:
                allowed_unes = getattr(effective_user, "allowed_unes", None) or getattr(effective_user, "unes", None)
            if allowed_unes and "une" in frame.columns:
                allowed = {str(item) for item in allowed_unes if item not in (None, "", [])}
                if allowed:
                    frame = frame[frame["une"].astype(str).isin(allowed)]
            return frame, list(frame.columns)

        conn = get_safe_connection()
        relation = data_scope_service.get_filtered_dataframe(effective_user, conn=conn)
        available_columns = list(relation.columns)
        schema = self.detect_transaction_schema(available_columns)
        selected_columns = [
            value
            for value in schema["selected_columns"].values()
            if value and value in available_columns
        ]
        selected_columns.extend(
            column
            for column in available_columns
            if column in {
                "NOME",
                "NOMECATEGORIA",
                "NOMESEGMENTO",
                "UNE",
                "TIPO",
                "SERIE",
                "PICKLIST",
                "ROMANEIO_SOLICITACAO",
                "ROMANEIO_ENVIO",
                "SOLICITACAO_PENDENTE",
            }
        )
        projection = list(dict.fromkeys(selected_columns))
        if not projection:
            return pd.DataFrame(), available_columns
        return relation.project(", ".join(projection)).df(), available_columns

    def _normalize_request(self, request: Any) -> dict[str, Any]:
        raw = self._to_mapping(request)
        return {
            "start_date": self._coerce_date(raw.get("start_date")),
            "end_date": self._coerce_date(raw.get("end_date")),
            "une": self._clean_optional_string(raw.get("une")),
            "segment": self._clean_optional_string(raw.get("segment")),
            "category": self._clean_optional_string(raw.get("category")),
            "target_product": self._clean_optional_string(raw.get("target_product")),
            "target_terms": self._clean_optional_string_list(raw.get("target_terms")),
            "min_support": self._clamp_float(raw.get("min_support"), default=0.01, minimum=0.0001, maximum=1.0),
            "min_confidence": self._clamp_float(raw.get("min_confidence"), default=0.2, minimum=0.0, maximum=1.0),
            "min_lift": self._clamp_float(raw.get("min_lift"), default=1.0, minimum=0.0, maximum=100.0),
            "max_rules": self._clamp_int(raw.get("max_rules"), default=20, minimum=1, maximum=100),
        }

    @staticmethod
    def _to_mapping(payload: Any) -> dict[str, Any]:
        if isinstance(payload, Mapping):
            return dict(payload)
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        if hasattr(payload, "dict"):
            return payload.dict()
        return {}

    @staticmethod
    def _coerce_date(value: Any) -> date | None:
        if value in (None, "", False):
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            return datetime.fromisoformat(str(value)).date()
        except ValueError:
            return None

    @staticmethod
    def _clamp_float(value: Any, *, default: float, minimum: float, maximum: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _clamp_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _clean_optional_string(value: Any) -> str | None:
        if value in (None, "", False):
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def _clean_optional_string_list(cls, value: Any) -> list[str]:
        if value in (None, "", False):
            return []
        if isinstance(value, str):
            candidates = re.split(r"[;,|]", value)
        elif isinstance(value, Sequence):
            candidates = list(value)
        else:
            candidates = [value]
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            text = cls._clean_optional_string(item)
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(text)
        return cleaned

    @staticmethod
    def _clean_key(value: Any) -> str | None:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return None
        return text

    @staticmethod
    def _normalize_column_name(column: Any) -> str:
        if not column:
            return ""
        normalized = unicodedata.normalize("NFKD", str(column))
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return re.sub(r"[^a-z0-9]+", "", normalized.lower())

    @staticmethod
    def _filter_rules_for_target(rules_df: pd.DataFrame, target_product: str) -> pd.DataFrame:
        if rules_df.empty:
            return rules_df
        target = str(target_product).casefold()
        mask = rules_df.apply(
            lambda row: any(str(item).casefold() == target for item in row["antecedents"])
            or any(str(item).casefold() == target for item in row["consequents"]),
            axis=1,
        )
        return rules_df[mask].reset_index(drop=True)

    @staticmethod
    def _filter_itemsets_for_target(itemsets_df: pd.DataFrame, target_product: str) -> pd.DataFrame:
        if itemsets_df.empty:
            return itemsets_df
        target = str(target_product).casefold()
        mask = itemsets_df["itemsets"].apply(
            lambda items: any(str(item).casefold() == target for item in items)
        )
        return itemsets_df[mask].reset_index(drop=True)

    @staticmethod
    def _filter_rules_for_terms(rules_df: pd.DataFrame, target_terms: Sequence[str]) -> pd.DataFrame:
        if rules_df.empty or not target_terms:
            return rules_df
        terms = [str(term).casefold() for term in target_terms if str(term).strip()]
        if not terms:
            return rules_df

        def matches(row: pd.Series) -> bool:
            items = [str(item).casefold() for item in row["antecedents"]] + [str(item).casefold() for item in row["consequents"]]
            return any(term in item for term in terms for item in items)

        return rules_df[rules_df.apply(matches, axis=1)].reset_index(drop=True)

    @staticmethod
    def _filter_itemsets_for_terms(itemsets_df: pd.DataFrame, target_terms: Sequence[str]) -> pd.DataFrame:
        if itemsets_df.empty or not target_terms:
            return itemsets_df
        terms = [str(term).casefold() for term in target_terms if str(term).strip()]
        if not terms:
            return itemsets_df
        mask = itemsets_df["itemsets"].apply(
            lambda items: any(term in str(item).casefold() for term in terms for item in items)
        )
        return itemsets_df[mask].reset_index(drop=True)

    @staticmethod
    def _serialize_itemsets(itemsets_df: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
        if itemsets_df.empty:
            return []
        ordered = itemsets_df.sort_values(["support"], ascending=False).head(limit)
        rows: list[dict[str, Any]] = []
        for _, row in ordered.iterrows():
            rows.append(
                {
                    "items": sorted(str(item) for item in row["itemsets"]),
                    "support": round(float(row["support"]), 4),
                    "size": int(len(row["itemsets"])),
                }
            )
        return rows

    @staticmethod
    def _serialize_rules(rules_df: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
        if rules_df.empty:
            return []
        ordered = rules_df.sort_values(["lift", "confidence", "support"], ascending=False).head(limit)
        rows: list[dict[str, Any]] = []
        for _, row in ordered.iterrows():
            rows.append(
                {
                    "antecedent": sorted(str(item) for item in row["antecedents"]),
                    "consequent": sorted(str(item) for item in row["consequents"]),
                    "support": round(float(row["support"]), 4),
                    "confidence": round(float(row["confidence"]), 4),
                    "lift": round(float(row["lift"]), 4),
                }
            )
        return rows
