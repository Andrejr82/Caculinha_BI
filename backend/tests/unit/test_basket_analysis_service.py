from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from backend.app.services.basket_analysis_service import BasketAnalysisService


class StaticBasketAnalysisService(BasketAnalysisService):
    def __init__(self, frame: pd.DataFrame):
        self._frame = frame

    def _load_source_frame(self, user=None):  # type: ignore[override]
        return self._frame.copy(), list(self._frame.columns)


def _build_strong_transaction_dataset(total_transactions: int = 120) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    base_date = date(2025, 1, 1)
    for idx in range(total_transactions):
        tx_id = f"TX-{idx:03d}"
        tx_date = base_date + timedelta(days=idx % 15)
        rows.append(
            {
                "TRANSACTION_ID": tx_id,
                "SKU": "caderno",
                "NOME": "Caderno",
                "DATA_VENDA": tx_date.isoformat(),
                "UNE": "135",
                "SEGMENTO": "PAPELARIA",
                "CATEGORIA": "ESCOLAR",
            }
        )
        rows.append(
            {
                "TRANSACTION_ID": tx_id,
                "SKU": "caneta",
                "NOME": "Caneta",
                "DATA_VENDA": tx_date.isoformat(),
                "UNE": "135",
                "SEGMENTO": "PAPELARIA",
                "CATEGORIA": "ESCOLAR",
            }
        )
        if idx % 3 == 0:
            rows.append(
                {
                    "TRANSACTION_ID": tx_id,
                    "SKU": "cola",
                    "NOME": "Cola",
                    "DATA_VENDA": tx_date.isoformat(),
                    "UNE": "135",
                    "SEGMENTO": "PAPELARIA",
                    "CATEGORIA": "ESCOLAR",
                }
            )
    return pd.DataFrame(rows)


def _build_sparse_nota_dataset() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(90):
        rows.append(
            {
                "NOTA": None,
                "PRODUTO": f"ITEM-{idx}",
                "NOTA_EMISSAO": None,
                "UNE": "135",
            }
        )
    for nota in range(5):
        rows.append({"NOTA": nota, "PRODUTO": "caderno", "NOTA_EMISSAO": "2025-07-11", "UNE": "135"})
        rows.append({"NOTA": nota, "PRODUTO": "caneta", "NOTA_EMISSAO": "2025-07-11", "UNE": "135"})
    return pd.DataFrame(rows)


def _build_subset_nota_dataset() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(4000):
        rows.append(
            {
                "NOTA": None,
                "PRODUTO": f"CAT-{idx}",
                "NOTA_EMISSAO": None,
                "UNE": "135",
                "TIPO": 2,
                "SERIE": "4",
                "PICKLIST": None,
                "ROMANEIO_SOLICITACAO": None,
                "ROMANEIO_ENVIO": None,
                "SOLICITACAO_PENDENTE": None,
            }
        )

    for nota in range(400):
        emission = "2025-07-14"
        rows.append(
            {
                "NOTA": nota,
                "PRODUTO": "caderno",
                "NOTA_EMISSAO": emission,
                "UNE": "135",
                "TIPO": 2,
                "SERIE": "4",
                "PICKLIST": 1,
                "ROMANEIO_SOLICITACAO": 1,
                "ROMANEIO_ENVIO": 1,
                "SOLICITACAO_PENDENTE": 1,
            }
        )
        rows.append(
            {
                "NOTA": nota,
                "PRODUTO": "caneta",
                "NOTA_EMISSAO": emission,
                "UNE": "135",
                "TIPO": 2,
                "SERIE": "4",
                "PICKLIST": 1,
                "ROMANEIO_SOLICITACAO": 1,
                "ROMANEIO_ENVIO": 1,
                "SOLICITACAO_PENDENTE": 1,
            }
        )
        if nota % 2 == 0:
            rows.append(
                {
                    "NOTA": nota,
                    "PRODUTO": "cola",
                    "NOTA_EMISSAO": emission,
                    "UNE": "135",
                    "TIPO": 2,
                    "SERIE": "4",
                    "PICKLIST": 1,
                    "ROMANEIO_SOLICITACAO": 1,
                    "ROMANEIO_ENVIO": 1,
                    "SOLICITACAO_PENDENTE": 1,
                }
            )
    return pd.DataFrame(rows)


def test_detect_transaction_schema_identifies_hypothesis_nota() -> None:
    service = BasketAnalysisService()
    schema = service.detect_transaction_schema(["NOTA", "PRODUTO", "NOTA_EMISSAO", "UNE"])

    assert schema["selected_columns"]["transaction_key"] == "NOTA"
    assert schema["selected_columns"]["product_key"] == "PRODUTO"
    assert schema["transaction_key_confidence"] == "hypothesis"


def test_build_transaction_frame_applies_filters() -> None:
    frame = _build_strong_transaction_dataset()
    service = StaticBasketAnalysisService(frame)
    schema = service.detect_transaction_schema(frame.columns)

    filtered = service.build_transaction_frame(
        frame,
        schema,
        {
            "start_date": date(2025, 1, 3),
            "end_date": date(2025, 1, 6),
            "une": "135",
            "segment": "PAPELARIA",
            "category": "ESCOLAR",
            "target_product": None,
            "min_support": 0.01,
            "min_confidence": 0.2,
            "min_lift": 1.0,
            "max_rules": 20,
        },
    )

    assert not filtered.empty
    assert filtered["transaction_date"].min().date() >= date(2025, 1, 3)
    assert filtered["transaction_date"].max().date() <= date(2025, 1, 6)
    assert filtered["segment"].str.upper().eq("PAPELARIA").all()


def test_service_generates_itemsets_and_rules_from_strong_dataset() -> None:
    frame = _build_strong_transaction_dataset()
    service = StaticBasketAnalysisService(frame)
    schema = service.detect_transaction_schema(frame.columns)
    transaction_frame = service.build_transaction_frame(
        frame,
        schema,
        {
            "start_date": None,
            "end_date": None,
            "une": None,
            "segment": None,
            "category": None,
            "target_product": None,
            "min_support": 0.2,
            "min_confidence": 0.6,
            "min_lift": 1.0,
            "max_rules": 10,
        },
    )
    basket_matrix = service.build_basket_matrix(transaction_frame)
    itemsets_df, algorithm = service.run_frequent_itemsets(basket_matrix, min_support=0.2)
    rules_df = service.run_association_rules(itemsets_df, min_confidence=0.6, min_lift=1.0, max_rules=10)

    assert algorithm in {"fpgrowth", "apriori", "manual_pairs"}
    assert any({"caderno", "caneta"} == set(row) for row in itemsets_df["itemsets"])
    assert not rules_df.empty
    assert any(set(row["antecedents"]) == {"caderno"} for _, row in rules_df.iterrows())


def test_analyze_returns_real_transactional_for_strong_dataset() -> None:
    service = StaticBasketAnalysisService(_build_strong_transaction_dataset())

    result = service.analyze(
        {
            "min_support": 0.2,
            "min_confidence": 0.6,
            "min_lift": 1.0,
            "max_rules": 10,
        },
        user=object(),
    )

    assert result["status"] == "success"
    assert result["analysis_mode"] == "real_transactional"
    assert result["transactions_analyzed"] == 120
    assert result["top_rules"]


def test_analyze_returns_subset_transactional_supported_for_controlled_nota_subset() -> None:
    service = StaticBasketAnalysisService(_build_subset_nota_dataset())

    result = service.analyze({}, user=object())

    assert result["status"] == "success"
    assert result["analysis_mode"] == "subset_transactional_supported"
    assert result["diagnostics"]["support"]["metrics"]["semantic_signals"]["transaction_column_is_nota"] is True
    assert result["diagnostics"]["support"]["metrics"]["logistics_signal_ratios"]["PICKLIST"] == 1.0
    assert any("subset controlado" in item.lower() for item in result["limitations"])


def test_analyze_returns_unsupported_for_sparse_nota_dataset() -> None:
    service = StaticBasketAnalysisService(_build_sparse_nota_dataset())

    result = service.analyze({}, user=object())

    assert result["status"] == "unsupported"
    assert result["analysis_mode"] == "unsupported"
    assert any("snapshot analitico" in item.lower() for item in result["limitations"])
