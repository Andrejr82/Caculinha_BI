"""
Teste final do endpoint de insights
Simula a chamada real que estava travando o navegador
"""

import sys
from pathlib import Path
import asyncio

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def test_insights_endpoint_real():
    """Testa o endpoint real de insights"""
    print("=" * 70)
    print("TESTE FINAL: Endpoint /insights/proactive")
    print("Simula a chamada que travava o navegador")
    print("=" * 70)
    
    try:
        # Importar o endpoint diretamente
        from app.api.v1.endpoints.insights import _generate_offline_insights
        
        print("\n[1/1] Executando _generate_offline_insights()...")
        print("      (Este metodo usa DataAggregationService internamente)")
        
        insights = await _generate_offline_insights()
        
        print(f"\nOK - Gerados {len(insights)} insights")
        print("\nInsights retornados:")
        print("-" * 70)
        
        for i, insight in enumerate(insights, 1):
            print(f"\n{i}. {insight.get('title')}")
            print(f"   Categoria: {insight.get('category')}")
            print(f"   Severidade: {insight.get('severity')}")
            print(f"   Descricao: {insight.get('description')[:80]}...")
            if insight.get('recommendation'):
                print(f"   Recomendacao: {insight.get('recommendation')[:60]}...")
        
        print("\n" + "=" * 70)
        print("SUCESSO!")
        print("O endpoint de insights esta funcionando sem travar.")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_insights_endpoint_real())
    exit(0 if result else 1)
