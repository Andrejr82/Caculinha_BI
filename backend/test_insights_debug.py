"""
Teste direto do LLMInsightsService para debug
"""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath('.'))

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_insights():
    try:
        from app.services.llm_insights import LLMInsightsService
        
        print("[TEST] Testando LLMInsightsService...")
        insights = await LLMInsightsService.generate_proactive_insights()
        
        print(f"[TEST] Insights gerados: {len(insights)}")
        for i, insight in enumerate(insights, 1):
            print(f"\n{i}. {insight.get('title')}")
            print(f"   {insight.get('description')[:100]}...")
            print(f"   Categoria: {insight.get('category')} | Severidade: {insight.get('severity')}")
        
        return insights
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_insights())
    if result and len(result) > 0:
        if result[0].get('title') == "Sistema de Insights em Manutencao":
            print("\n[FAIL] Retornou fallback - sistema com erro!")
        else:
            print(f"\n[SUCCESS] Teste concluido! {len(result)} insights gerados.")
    else:
        print("\n[FAIL] Teste falhou!")
