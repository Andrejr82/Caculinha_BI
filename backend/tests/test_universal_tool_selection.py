"""
Teste do Sistema Universal de Seleção de Ferramentas
Valida Intent Classifier e Query Router com queries reais.

Author: QA Automation Engineer Agent
Date: 2026-01-24
"""

import pytest
from backend.app.core.utils.intent_classifier import classify_intent, IntentType
from backend.app.core.utils.query_router import route_query


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
        
        assert selection.tool_name == "prever_demanda_sazonal"
        assert "produto_codigo" in selection.tool_params
        assert selection.tool_params["produto_codigo"] == 25  # Int
        assert "dias_previsao" in selection.tool_params
        assert selection.tool_params["dias_previsao"] == 30  # Int
    
    def test_calculation_routing(self):
        """Testa roteamento de cálculos."""
        query = "calcule o lote econômico para o produto 369947"
        intent_result = classify_intent(query)
        
        selection = route_query(intent_result.intent, query, intent_result.confidence)
        
        assert selection.tool_name == "calcular_eoq"
        assert "produto_codigo" in selection.tool_params
        assert selection.tool_params["produto_codigo"] == 369947  # Int
    
    def test_parameter_extraction(self):
        """Testa extração de parâmetros complexos."""
        query = "gere um gráfico de top 5 produtos do segmento PAPELARIA na loja 1685"
        intent_result = classify_intent(query)
        
        selection = route_query(intent_result.intent, query, intent_result.confidence)
        
        assert selection.tool_params["filtro_une"] == "1685"  # String
        assert selection.tool_params["filtro_segmento"] == "PAPELARIA"  # String
        assert selection.tool_params["limite"] == "5"  # String (compat provider strict schema)


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
