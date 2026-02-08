"""
Test Suite for Purchasing Tools and CodeGenAgent

Testes unitários para validar funcionalidades de cálculos complexos.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

# Importar módulos a testar
from backend.app.core.agents.code_gen_agent import CodeGenAgent, get_code_gen_agent
from backend.app.core.utils.seasonality_detector import (
    detect_seasonal_context,
    get_seasonal_recommendation,
    get_all_upcoming_seasons
)


class TestCodeGenAgent:
    """Testes para CodeGenAgent"""
    
    def test_singleton_pattern(self):
        """Testa que get_code_gen_agent retorna sempre a mesma instância"""
        agent1 = get_code_gen_agent()
        agent2 = get_code_gen_agent()
        assert agent1 is agent2
    
    def test_eoq_calculation(self):
        """Testa cálculo de EOQ"""
        agent = get_code_gen_agent()
        result = agent.calculate_eoq_internal(
            demand_annual=12000,
            order_cost=150,
            holding_cost_pct=0.25,
            unit_cost=10
        )
        
        assert "eoq" in result
        assert result["eoq"] > 0
        assert "orders_per_year" in result
        assert "total_cost" in result
    
    def test_forecast_with_insufficient_data(self):
        """Testa que previsão falha com dados insuficientes"""
        agent = get_code_gen_agent()
        
        # Criar DataFrame com poucos dados
        data = pd.DataFrame({
            'VENDA_30DD': [100, 110, 105]
        })
        
        result = agent.execute_forecast(data, periods=30)
        
        # Deve retornar erro
        assert "error" in result or len(result.get("forecast", [])) == 0
    
    def test_forecast_with_valid_data(self):
        """Testa previsão com dados válidos"""
        agent = get_code_gen_agent()
        
        # Criar série temporal sintética (365 dias)
        np.random.seed(42)
        dates = pd.date_range('2025-01-01', periods=365, freq='D')
        sales = 100 + np.random.randn(365) * 10 + np.sin(np.arange(365) * 2 * np.pi / 365) * 20
        
        data = pd.DataFrame({
            'VENDA_30DD': sales
        })
        
        result = agent.execute_forecast(data, periods=30)
        
        assert "forecast" in result
        assert len(result["forecast"]) == 30
        assert "accuracy" in result
        assert "model" in result
    
    def test_security_validation(self):
        """Testa validação de segurança do sandbox"""
        agent = get_code_gen_agent()
        security = agent.validate_sandbox_security()
        
        assert "filesystem_blocked" in security
        assert "timeout_works" in security
        assert "whitelist_enforced" in security
        
        # Filesystem deve estar bloqueado
        assert security["filesystem_blocked"] == True


class TestSeasonalityDetector:
    """Testes para Detector de Sazonalidade"""
    
    def test_volta_as_aulas_detection(self):
        """Testa detecção de Volta às Aulas"""
        # Janeiro
        context = detect_seasonal_context(datetime(2026, 1, 15))
        
        assert context is not None
        assert context["season"] == "volta_as_aulas"
        assert context["multiplier"] == 2.5
        assert context["urgency"] == "ALTA"
    
    def test_natal_detection(self):
        """Testa detecção de Natal"""
        # Dezembro
        context = detect_seasonal_context(datetime(2026, 12, 10))
        
        assert context is not None
        assert context["season"] == "natal"
        assert context["multiplier"] == 3.0
        assert context["urgency"] == "CRÍTICA"
    
    def test_no_season_detection(self):
        """Testa que retorna None fora de períodos sazonais"""
        # Junho (sem período sazonal)
        context = detect_seasonal_context(datetime(2026, 6, 15))
        
        assert context is None
    
    def test_seasonal_recommendation(self):
        """Testa recomendação com ajuste sazonal"""
        base_qty = 1000
        
        # Simular contexto de Volta às Aulas
        seasonal_context = {
            "season": "volta_as_aulas",
            "multiplier": 2.5,
            "urgency": "ALTA",
            "is_peak_period": True
        }
        
        recommendation = get_seasonal_recommendation(base_qty, seasonal_context)
        
        assert recommendation["recommended_quantity"] > base_qty
        assert recommendation["adjustment_factor"] >= 2.5
        assert "reasoning" in recommendation
    
    def test_upcoming_seasons(self):
        """Testa listagem de próximos períodos sazonais"""
        upcoming = get_all_upcoming_seasons(months_ahead=6)
        
        assert isinstance(upcoming, list)
        assert len(upcoming) > 0
        
        # Deve estar ordenado por proximidade
        if len(upcoming) > 1:
            assert upcoming[0]["months_until"] <= upcoming[1]["months_until"]


# Executar testes se rodado diretamente
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
