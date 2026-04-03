"""
Teste do Sistema Universal de Seleção de Ferramentas
Valida Intent Classifier e Query Router com queries reais.

Author: QA Automation Engineer Agent
Date: 2026-01-24
"""

import pytest
from backend.app.core.utils.intent_classifier import classify_intent, IntentType
from backend.app.core.utils.query_router import (
    route_query,
    extract_une_filter,
    extract_chart_breakdown,
    extract_segment_filter,
    is_all_stores_scope,
    extract_period_filter,
    extract_top_limit,
    is_product_rupture_query,
    is_product_store_leader_query,
    is_explicit_table_request,
    map_breakdown_to_group_column,
)


class TestIntentClassifier:
    """Testes do Intent Classifier."""
    
    def test_visualization_intent(self):
        """Testa detecção de intenção de visualização."""
        queries = [
            "gere um gráfico de ranking de vendas dos segmentos na une 520",
            "mostre um gráfico de vendas por categoria",
            "top 10 produtos mais vendidos",
            "ranking de vendas"
        ]
        
        for query in queries:
            result = classify_intent(query)
            assert result.intent == IntentType.VISUALIZATION, f"Failed for: {query}"
            assert result.confidence > 0.80, f"Low confidence for: {query}"
    
    def test_forecasting_intent(self):
        """Testa detecção de intenção de previsão."""
        queries = [
            "qual a previsão de vendas do produto 25?",
            "forecast para próximos 30 dias",
            "quanto vai vender na volta às aulas?",
            "previsão de demanda"
        ]
        
        for query in queries:
            result = classify_intent(query)
            assert result.intent == IntentType.FORECASTING, f"Failed for: {query}"
            assert result.confidence > 0.75
    
    def test_calculation_intent(self):
        """Testa detecção de intenção de cálculo."""
        queries = [
            "calcule o lote econômico do produto 369947",
            "quanto comprar de produto X?",
            "qual o EOQ?",
            "margem de contribuição do produto 25",
            "Se eu der 10% de desconto em um produto com margem atual de 28%, como fica a margem estimada?",
        ]
        
        for query in queries:
            result = classify_intent(query)
            assert result.intent == IntentType.CALCULATION, f"Failed for: {query}"
            assert result.confidence > 0.80

    def test_comparison_intent_defaults_to_analysis_without_chart_request(self):
        result = classify_intent("compare vendas entre lojas")
        assert result.intent == IntentType.ANALYSIS
        assert result.confidence >= 0.85
    
    def test_anomaly_detection_intent(self):
        """Testa detecção de intenção de anomalia."""
        queries = [
            "detecte vendas anormais do produto 369947",
            "houve picos de venda?",
            "identifique outliers nos últimos 90 dias"
        ]
        
        for query in queries:
            result = classify_intent(query)
            assert result.intent == IntentType.ANOMALY_DETECTION, f"Failed for: {query}"
            assert result.confidence > 0.85

    def test_visualization_intent_handles_typo_all_stores_query(self):
        """Query real com typo deve cair em visualização (não data_query)."""
        query = "me de um grafico de vendas do segmento artes de toas as unes"
        result = classify_intent(query)
        assert result.intent == IntentType.VISUALIZATION
        assert result.confidence >= 0.90

    def test_table_request_intent_is_not_left_in_fallback_mode(self):
        query = "me mostre em tabela as vendas por loja do segmento tecidos nos ultimos 30 dias"
        result = classify_intent(query)

        assert result.intent == IntentType.DATA_QUERY
        assert result.confidence >= 0.90


class TestQueryRouter:
    """Testes do Query Router."""
    
    def test_visualization_routing(self):
        """Testa roteamento de visualizações."""
        query = "gere um gráfico de ranking de vendas dos segmentos na une 520"
        intent_result = classify_intent(query)
        
        selection = route_query(intent_result.intent, query, intent_result.confidence)
        
        assert selection.tool_name == "gerar_grafico_universal_v2"
        assert "filtro_une" in selection.tool_params
        assert selection.tool_params["filtro_une"] == "520"  # String
        assert "limite" in selection.tool_params
        assert selection.confidence > 0.85

    def test_extract_une_filter_accepts_textual_store_codes(self):
        assert extract_une_filter("gere um relatório de vendas do segmento tecidos na une scr") == "SCR"
        assert extract_une_filter("mostre as vendas da loja mad") == "MAD"

    def test_analysis_routing_keeps_textual_une_as_filter(self):
        query = "gere um relatório de vendas do segmento tecidos na une scr"
        intent_result = classify_intent(query)

        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "consultar_dados_flexivel"
        assert selection.tool_params["filtros"]["UNE"] == "SCR"
        assert selection.tool_params["filtros"]["NOMESEGMENTO"] == "TECIDOS"
    
    def test_forecasting_routing(self):
        """Testa roteamento de previsões."""
        query = "qual a previsão de vendas do produto 25 para os próximos 30 dias?"
        intent_result = classify_intent(query)
        
        selection = route_query(intent_result.intent, query, intent_result.confidence)
        
        assert selection.tool_name == "prever_demanda"
        assert "produto_id" in selection.tool_params
        assert selection.tool_params["produto_id"] == "25"  # String
        assert "periodo_dias" in selection.tool_params
        assert selection.tool_params["periodo_dias"] == 30  # Int
    
    def test_calculation_routing(self):
        """Testa roteamento de cálculos."""
        query = "calcule o lote econômico para o produto 369947"
        intent_result = classify_intent(query)
        
        selection = route_query(intent_result.intent, query, intent_result.confidence)
        
        assert selection.tool_name == "calcular_eoq"
        assert "produto_id" in selection.tool_params
        assert selection.tool_params["produto_id"] == "369947"  # String

    def test_calculation_routing_for_mc_uses_direct_tool(self):
        query = "qual a média comum do produto 369947 na une 520"
        intent_result = classify_intent(query)

        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "calcular_mc_produto"
        assert selection.tool_params["produto_id"] == 369947
        assert selection.tool_params["une_id"] == 520

    def test_calculation_routing_for_operational_metrics_uses_flexible_query_snapshot(self):
        query = "calcule o giro de estoque do produto 369947 na une 520"
        intent_result = classify_intent(query)

        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "consultar_dados_flexivel"
        assert "colunas" in selection.tool_params
        assert "ESTOQUE_UNE" in selection.tool_params["colunas"]
        assert selection.tool_params["filtros"]["PRODUTO"] == 369947
        assert selection.tool_params["filtros"]["UNE"] == 520

    def test_calculation_routing_for_price_policy_uses_direct_price_tool(self):
        query = "calcule o preço final para compra de 1000 no ranking 2 à vista"
        intent_result = classify_intent(query)

        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "calcular_preco_final_une"
        assert selection.tool_params["valor_compra"] == 1000.0
        assert selection.tool_params["ranking"] == 2
        assert selection.tool_params["forma_pagamento"] == "vista"
    
    def test_parameter_extraction(self):
        """Testa extração de parâmetros complexos."""
        query = "gere um gráfico de top 5 produtos do segmento PAPELARIA na loja 1685"
        intent_result = classify_intent(query)
        
        selection = route_query(intent_result.intent, query, intent_result.confidence)
        
        assert selection.tool_params["filtro_une"] == "1685"  # String
        assert selection.tool_params["filtro_segmento"] == "PAPELARIA"  # String
        assert selection.tool_params["limite"] == "5"  # String (compat provider strict schema)

    def test_dashboard_routing_with_segment_and_period(self):
        query = "crie um dashboard interativo do segmento ARTES para os ultimos 30 dias"
        intent_result = classify_intent(query)

        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "gerar_dashboard_executivo"
        assert selection.tool_params.get("segmento") == "ARTES"
        assert selection.tool_params.get("periodo") == "30d"

    def test_extract_segment_filter_handles_all_stores_typo(self):
        """Segmento deve ser extraído sem capturar 'toas/todas as unes/lojas'."""
        query = "me de um grafico de vendas do segmento artes de toas as unes"
        assert extract_segment_filter(query) == "ARTES"

    def test_extract_segment_filter_ignores_each_store_suffix(self):
        query = "me de o gráfico de vendas do segmento tecidos de cada loja"
        assert extract_segment_filter(query) == "TECIDOS"
        assert extract_chart_breakdown(query) == "LOJA"

    def test_extract_chart_breakdown_prefers_store_when_segment_is_filter_and_scope_is_all_stores(self):
        query = "gere um gráfico de vendas do segmento tecidos em todas as lojas nos últimos 30 dias"
        assert extract_segment_filter(query) == "TECIDOS"
        assert is_all_stores_scope(query) is True
        assert extract_chart_breakdown(query) == "LOJA"
        assert is_explicit_table_request("me mostre em tabela as vendas por loja do segmento tecidos") is True
        assert map_breakdown_to_group_column("LOJA") == "UNE"

    def test_extract_segment_filter_handles_segment_typos(self):
        query = "ger eum gráfico de vendas do ssegmento festas de cada loja"
        assert extract_segment_filter(query) == "FESTAS"
        assert extract_chart_breakdown(query) == "LOJA"

    def test_detect_all_stores_scope_handles_typo(self):
        """Detector de escopo toda rede deve tolerar typo comum."""
        query = "grafico de vendas do segmento artes de toas as unes"
        assert is_all_stores_scope(query) is True

    def test_extract_period_filter(self):
        assert extract_period_filter("dashboard dos ultimos 15 dias") == "15d"
        assert extract_period_filter("dashboard das ultimas 8 semanas") == "8w"
        assert extract_period_filter("dashboard dos ultimos 6 meses") == "6m"

    def test_extract_top_limit_handles_store_ranking_phrase(self):
        assert extract_top_limit("quais 5 lojas mais vendem o produto 59294") == 5

    def test_product_rupture_query_detects_specific_product(self):
        assert is_product_rupture_query("quais lojas estão com rupturas do produto 369947") is True

    def test_product_store_leader_query_detects_typo_and_prefers_store_breakdown(self):
        query = "qual loja mais vede o produto 369947 ?"
        assert is_product_store_leader_query(query) is True
        assert extract_chart_breakdown(query) == "LOJA"


class TestEndToEnd:
    """Testes end-to-end do sistema completo."""
    
    def test_user_query_original(self):
        """Testa a query original do usuário que falhou."""
        query = "gere um gráfico de ranking de vendas dos segmentos na une 520"
        
        # Classificar intent
        intent_result = classify_intent(query)
        assert intent_result.intent == IntentType.VISUALIZATION
        assert intent_result.confidence > 0.90
        
        # Rotear para ferramenta
        selection = route_query(intent_result.intent, query, intent_result.confidence)
        assert selection.tool_name == "gerar_grafico_universal_v2"
        assert selection.confidence > 0.85  # Deve acionar forced execution
        
        # Verificar parâmetros extraídos
        assert selection.tool_params["filtro_une"] == "520"
        assert "ranking" in selection.tool_params["descricao"].lower()
        assert selection.tool_params["tipo_grafico"] == "bar"

    def test_segment_scope_query_does_not_infer_bogus_segment_filter(self):
        query = "gere um gráfico de vendas dos segmentos da une 520"

        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "gerar_grafico_universal_v2"
        assert selection.tool_params["filtro_une"] == "520"
        assert selection.tool_params["quebra_por"] == "SEGMENTO"
        assert "filtro_segmento" not in selection.tool_params

    def test_user_query_typo_chart_still_routes_to_chart_tool(self):
        """A query com typo deve escolher ferramenta de gráfico com filtro de segmento."""
        query = "me de um grafico de vendas do segmento artes de toas as unes"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "gerar_grafico_universal_v2"
        assert selection.tool_params.get("filtro_segmento") == "ARTES"

    def test_store_breakdown_query_with_segment_suffix_routes_correctly(self):
        query = "me de o gráfico de vendas do segmento tecidos de cada loja"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "gerar_grafico_universal_v2"
        assert selection.tool_params.get("filtro_segmento") == "TECIDOS"
        assert selection.tool_params.get("quebra_por") == "LOJA"

    def test_explicit_table_request_by_store_routes_to_aggregated_table_query(self):
        query = "me mostre em tabela as vendas por loja do segmento tecidos nos ultimos 30 dias"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "consultar_dados_flexivel"
        assert selection.tool_params.get("agregacao") == "SUM"
        assert selection.tool_params.get("coluna_agregacao") == "VENDA_30DD"
        assert selection.tool_params.get("agrupar_por") == ["UNE"]
        assert selection.tool_params.get("filtros", {}).get("NOMESEGMENTO") == "TECIDOS"

    def test_store_breakdown_query_with_segment_typo_routes_correctly(self):
        query = "ger eum gráfico de vendas do ssegmento festas de cada loja"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "gerar_grafico_universal_v2"
        assert selection.tool_params.get("filtro_segmento") == "FESTAS"
        assert selection.tool_params.get("quebra_por") == "LOJA"

    def test_product_store_leader_query_routes_to_multi_store_analysis(self):
        query = "qual loja mais vende o produto 369947 ?"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "analisar_produto_todas_lojas"
        assert selection.tool_params.get("produto_codigo") == 369947

    def test_product_store_leader_query_with_typo_routes_to_multi_store_analysis(self):
        query = "qual loja mais vede o produto 369947 ?"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "analisar_produto_todas_lojas"
        assert selection.tool_params.get("produto_codigo") == 369947

    def test_top_five_product_store_query_routes_to_aggregated_store_ranking(self):
        query = "quais 5 lojas mais vendem o produto 59294"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "consultar_dados_flexivel"
        assert selection.tool_params.get("agrupar_por") == ["UNE"]
        assert selection.tool_params.get("ordem_desc") is True
        assert selection.tool_params.get("limite") == 5
        assert selection.tool_params.get("filtros", {}).get("PRODUTO") == 59294

    def test_lowest_product_store_query_routes_to_bottom_store_ranking(self):
        query = "qual loja vende menos o produto 369947"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "consultar_dados_flexivel"
        assert selection.tool_params.get("agrupar_por") == ["UNE"]
        assert selection.tool_params.get("ordem_desc") is False
        assert selection.tool_params.get("limite") == 1
        assert selection.tool_params.get("filtros", {}).get("PRODUTO") == 369947

    def test_product_rupture_query_routes_to_multi_store_analysis(self):
        query = "quais lojas estão com rupturas do produto 369947"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "analisar_produto_todas_lojas"
        assert selection.tool_params.get("produto_codigo") == 369947

    def test_all_stores_scope_does_not_override_segment_breakdown(self):
        query = "gere um gráfico de vendas de todos os segmentos em todas as unes"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert extract_chart_breakdown(query) == "SEGMENTO"
        assert selection.tool_name == "gerar_grafico_universal_v2"
        assert selection.tool_params.get("quebra_por") == "SEGMENTO"

    def test_ruptura_query_routes_to_specialized_tool(self):
        """Perguntas de ruptura devem usar ferramenta dedicada."""
        query = "quais grupos estão com maior porcentagem de rupturas?"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "encontrar_rupturas_criticas"
        assert "limite" in selection.tool_params

    def test_negative_sales_with_typo_routes_without_generic_error_path(self):
        """Perguntas com typo sobre vendas ruins devem cair em rota acionável."""
        query = "quais grupos estão com as vendaas ruins?"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "consultar_dados_flexivel"
        assert selection.tool_params.get("agregacao") == "SUM"
        assert selection.tool_params.get("coluna_agregacao") == "VENDA_30DD"
        assert "NOMEGRUPO" in selection.tool_params.get("agrupar_por", [])
        assert selection.confidence >= 0.80


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
