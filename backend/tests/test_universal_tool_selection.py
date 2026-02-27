"""
Teste do Sistema Universal de Seleção de Ferramentas
Valida Intent Classifier e Query Router com queries reais.

Author: QA Automation Engineer Agent
Date: 2026-01-24
"""

import pytest
from backend.app.core.utils.intent_classifier import classify_intent, IntentType
from backend.app.core.utils.query_router import route_query, extract_segment_filter, is_all_stores_scope


class TestIntentClassifier:
    """Testes do Intent Classifier."""
    
    def test_visualization_intent(self):
        """Testa detecção de intenção de visualização."""
        queries = [
            "gere um gráfico de ranking de vendas dos segmentos na une 520",
            "mostre um gráfico de vendas por categoria",
            "top 10 produtos mais vendidos",
            "ranking de vendas",
            "compare vendas entre lojas"
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
            "margem de contribuição do produto 25"
        ]
        
        for query in queries:
            result = classify_intent(query)
            assert result.intent == IntentType.CALCULATION, f"Failed for: {query}"
            assert result.confidence > 0.80
    
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
    
    def test_parameter_extraction(self):
        """Testa extração de parâmetros complexos."""
        query = "gere um gráfico de top 5 produtos do segmento PAPELARIA na loja 1685"
        intent_result = classify_intent(query)
        
        selection = route_query(intent_result.intent, query, intent_result.confidence)
        
        assert selection.tool_params["filtro_une"] == "1685"  # String
        assert selection.tool_params["filtro_segmento"] == "PAPELARIA"  # String
        assert selection.tool_params["limite"] == "5"  # String (compat provider strict schema)

    def test_extract_segment_filter_handles_all_stores_typo(self):
        """Segmento deve ser extraído sem capturar 'toas/todas as unes/lojas'."""
        query = "me de um grafico de vendas do segmento artes de toas as unes"
        assert extract_segment_filter(query) == "ARTES"

    def test_detect_all_stores_scope_handles_typo(self):
        """Detector de escopo toda rede deve tolerar typo comum."""
        query = "grafico de vendas do segmento artes de toas as unes"
        assert is_all_stores_scope(query) is True


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

    def test_user_query_typo_chart_still_routes_to_chart_tool(self):
        """A query com typo deve escolher ferramenta de gráfico com filtro de segmento."""
        query = "me de um grafico de vendas do segmento artes de toas as unes"
        intent_result = classify_intent(query)
        selection = route_query(intent_result.intent, query, intent_result.confidence)

        assert selection.tool_name == "gerar_grafico_universal_v2"
        assert selection.tool_params.get("filtro_segmento") == "ARTES"

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
