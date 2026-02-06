"""
Teste completo do sistema de insights com debug detalhado
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath('.'))

async def test_insights_complete():
    print("\n=== TESTE COMPLETO DO SISTEMA DE INSIGHTS ===\n")
    
    try:
        from app.services.llm_insights import LLMInsightsService
        from app.services.data_aggregation import DataAggregationService
        
        # Passo 1: Testar agregacao de dados
        print("[1/2] Testando agregacao de dados...")
        data_summary = DataAggregationService.get_retail_summary()
        
        if "error" in data_summary:
            print(f"[ERRO] Erro na agregacao: {data_summary['error']}")
            return False
        
        print(f"[OK] Dados agregados:")
        print(f"     - Vendas 30d: {data_summary['general_stats']['total_sales_30d']}")
        print(f"     - Estoque: {data_summary['general_stats']['total_stock_units']}")
        print(f"     - Top produtos: {len(data_summary['top_performing_products'])}")
        
        # Passo 2: Testar geracao de insights
        print("\n[2/2] Gerando insights com LLM...")
        insights = await LLMInsightsService.generate_proactive_insights()
        
        print(f"\n[RESULTADO] {len(insights)} insights gerados:")
        for i, insight in enumerate(insights, 1):
            print(f"\n{i}. {insight.get('title')}")
            print(f"   Categoria: {insight.get('category')} | Severidade: {insight.get('severity')}")
            print(f"   Descricao: {insight.get('description')[:100]}...")
            if insight.get('recommendation'):
                print(f"   Recomendacao: {insight.get('recommendation')[:80]}...")
        
        # Verificar se e fallback
        if insights[0].get('title') == "Sistema de Insights em Manutencao":
            print("\n[AVISO] Sistema retornou fallback!")
            return False
        
        print("\n[SUCESSO] Sistema de insights funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_insights_complete())
    print(f"\n{'='*50}")
    print(f"Resultado Final: {'SUCESSO' if success else 'FALHA'}")
    print(f"{'='*50}\n")
