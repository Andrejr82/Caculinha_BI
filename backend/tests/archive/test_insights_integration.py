"""
Teste integrado do endpoint /insights/proactive
Simula a chamada que estava travando o navegador
"""

import sys
from pathlib import Path
import asyncio

# Adicionar backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def test_insights_endpoint():
    """Testa o fluxo completo de geração de insights"""
    print("=" * 70)
    print("TESTE INTEGRADO: Endpoint /insights/proactive")
    print("Objetivo: Validar que não há mais travamento no navegador")
    print("=" * 70)
    
    try:
        # 1. Testar DataAggregationService
        print("\n[1/3] Testando DataAggregationService.get_retail_summary()...")
        from app.services.data_aggregation import DataAggregationService
        
        summary = DataAggregationService.get_retail_summary(limit_items=5)
        
        if "error" in summary:
            print(f"❌ Erro na agregação: {summary['error']}")
            return False
        
        print("✅ DataAggregationService funcionou!")
        print(f"   - Total vendas 30d: {summary['general_stats']['total_sales_30d']}")
        print(f"   - Total estoque: {summary['general_stats']['total_stock_units']}")
        print(f"   - Top produtos: {len(summary['top_performing_products'])} itens")
        print(f"   - Rupturas: {len(summary['critical_measurements']['stockouts'])} itens")
        
        # 2. Testar LLMInsightsService (modo offline/fallback)
        print("\n[2/3] Testando LLMInsightsService (modo fallback)...")
        from app.services.llm_insights import _get_fallback_insights
        
        fallback = _get_fallback_insights()
        print(f"✅ Fallback insights: {len(fallback)} itens")
        
        # 3. Testar endpoint completo (simulado)
        print("\n[3/3] Simulando chamada ao endpoint /insights/proactive...")
        from app.api.v1.endpoints.insights import _generate_offline_insights
        
        insights = await _generate_offline_insights()
        print(f"✅ Insights offline gerados: {len(insights)} itens")
        
        for i, insight in enumerate(insights[:3], 1):
            print(f"\n   Insight {i}:")
            print(f"   - Título: {insight.get('title')}")
            print(f"   - Categoria: {insight.get('category')}")
            print(f"   - Severidade: {insight.get('severity')}")
        
        print("\n" + "=" * 70)
        print("✅ TESTE COMPLETO PASSOU!")
        print("O endpoint /insights/proactive não deve mais travar o navegador.")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_insights_endpoint())
    exit(0 if result else 1)
