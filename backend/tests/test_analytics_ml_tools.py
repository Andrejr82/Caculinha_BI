import pandas as pd

from backend.app.core.tools import advanced_analytics_tool as analytics_tool
from backend.app.core.tools.purchasing_tools import _allocate_stock_dataframe, _build_forecast_series
from backend.app.core.utils.tool_scoping import ToolPermissionManager


def test_segment_records_by_performance_groups_all_entities():
    records = [
        {"UNE": 101, "VENDA_30DD": 1200, "ESTOQUE_UNE": 300},
        {"UNE": 102, "VENDA_30DD": 1150, "ESTOQUE_UNE": 320},
        {"UNE": 201, "VENDA_30DD": 600, "ESTOQUE_UNE": 210},
        {"UNE": 202, "VENDA_30DD": 580, "ESTOQUE_UNE": 190},
        {"UNE": 301, "VENDA_30DD": 140, "ESTOQUE_UNE": 20},
        {"UNE": 302, "VENDA_30DD": 120, "ESTOQUE_UNE": 18},
    ]

    result = analytics_tool.segment_records_by_performance(records, num_clusters=3)

    assert "clusters" in result
    assert len(result["clusters"]) == len(records)
    assert result["num_clusters"] >= 2
    assert len({item["cluster_nome"] for item in result["clusters"]}) >= 2


def test_classify_stock_risk_identifies_priority_classes():
    records = [
        {"UNE": 101, "VENDA_30DD": 300, "ESTOQUE_UNE": 0},
        {"UNE": 102, "VENDA_30DD": 300, "ESTOQUE_UNE": 45},
        {"UNE": 103, "VENDA_30DD": 300, "ESTOQUE_UNE": 420},
        {"UNE": 104, "VENDA_30DD": 0, "ESTOQUE_UNE": 180},
    ]

    result = analytics_tool.classify_stock_risk(records, horizonte_dias=30)
    by_store = {item["entidade"]: item["classe_risco"] for item in result["classificacoes"]}

    assert by_store["101"] == "critico"
    assert by_store["102"] == "alto_risco"
    assert by_store["103"] == "saudavel"
    assert by_store["104"] == "excesso"


def test_build_forecast_series_is_deterministic_and_non_negative():
    first = _build_forecast_series(venda_diaria=12.5, periodo_dias=14, random_seed=7)
    second = _build_forecast_series(venda_diaria=12.5, periodo_dias=14, random_seed=7)

    assert first == second
    assert len(first) == 14
    assert all(value >= 0 for value in first)


def test_allocate_stock_dataframe_prioritizes_lower_coverage():
    stores = pd.DataFrame(
        [
            {"UNE": 101, "total_vendas": 300.0, "estoque_atual": 10.0},
            {"UNE": 102, "total_vendas": 300.0, "estoque_atual": 120.0},
            {"UNE": 103, "total_vendas": 180.0, "estoque_atual": 60.0},
        ]
    )

    allocated = _allocate_stock_dataframe(stores, quantidade_total=90, criterio="prioridade_ruptura")
    allocation_map = {int(row["UNE"]): int(row["alocacao"]) for _, row in allocated.iterrows()}

    assert allocation_map[101] >= allocation_map[102]
    assert sum(allocation_map.values()) == 90


def test_analise_regressao_vendas_accepts_resultados_schema(monkeypatch):
    def _fake_query(**kwargs):
        return {
            "resultados": [
                {"UNE": 101, "VENDA_30DD": 120.0, "ESTOQUE_UNE": 40.0, "NOME": "Produto A"},
                {"UNE": 102, "VENDA_30DD": 140.0, "ESTOQUE_UNE": 30.0, "NOME": "Produto A"},
                {"UNE": 103, "VENDA_30DD": 135.0, "ESTOQUE_UNE": 20.0, "NOME": "Produto A"},
                {"UNE": 104, "VENDA_30DD": 150.0, "ESTOQUE_UNE": 25.0, "NOME": "Produto A"},
            ]
        }

    monkeypatch.setattr("backend.app.core.tools.flexible_query_tool.consultar_dados_flexivel", _fake_query)

    tool_fn = getattr(analytics_tool.analise_regressao_vendas, "func", analytics_tool.analise_regressao_vendas)
    result = tool_fn(produto_id="25")

    assert result["total_lojas"] == 4
    assert result["media_vendas_30d"] > 0
    assert len(result["top_5_lojas"]) == 4


def test_segmentar_lojas_por_performance_accepts_resultados_schema(monkeypatch):
    def _fake_query(**kwargs):
        return {
            "resultados": [
                {"UNE": 101, "VENDA_30DD": 900.0, "ESTOQUE_UNE": 260.0},
                {"UNE": 102, "VENDA_30DD": 870.0, "ESTOQUE_UNE": 240.0},
                {"UNE": 201, "VENDA_30DD": 420.0, "ESTOQUE_UNE": 110.0},
                {"UNE": 202, "VENDA_30DD": 390.0, "ESTOQUE_UNE": 120.0},
                {"UNE": 301, "VENDA_30DD": 90.0, "ESTOQUE_UNE": 12.0},
            ]
        }

    monkeypatch.setattr("backend.app.core.tools.flexible_query_tool.consultar_dados_flexivel", _fake_query)

    tool_fn = getattr(
        analytics_tool.segmentar_lojas_por_performance,
        "func",
        analytics_tool.segmentar_lojas_por_performance,
    )
    result = tool_fn(produto_id="25", num_clusters=3)

    assert result["produto"] == "25"
    assert len(result["clusters"]) == 5


def test_analyst_scope_includes_new_ml_tools():
    allowed = set(ToolPermissionManager.list_available_tools("analyst"))

    assert "segmentar_lojas_por_performance" in allowed
    assert "classificar_risco_estoque" in allowed
