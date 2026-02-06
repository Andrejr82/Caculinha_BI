"""
Teste detalhado para identificar onde esta o erro no sistema de insights
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_step_by_step():
    print("\n=== TESTE PASSO A PASSO DO SISTEMA DE INSIGHTS ===\n")
    
    # Passo 1: Testar DataAggregationService
    print("[1/3] Testando DataAggregationService...")
    try:
        from app.services.data_aggregation import DataAggregationService
        
        data_summary = DataAggregationService.get_retail_summary()
        
        if "error" in data_summary:
            print(f"[ERRO] DataAggregationService retornou erro: {data_summary['error']}")
            return False
        else:
            print(f"[OK] Dados agregados com sucesso!")
            print(f"     - Total vendas 30d: {data_summary['general_stats']['total_sales_30d']}")
            print(f"     - Total estoque: {data_summary['general_stats']['total_stock_units']}")
            print(f"     - Top produtos: {len(data_summary['top_performing_products'])}")
            print(f"     - Rupturas: {len(data_summary['critical_measurements']['stockouts'])}")
    except Exception as e:
        print(f"[ERRO] Excecao em DataAggregationService: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Passo 2: Testar LLMFactory
    print("\n[2/3] Testando LLMFactory (Groq)...")
    try:
        from app.core.llm_factory import LLMFactory
        
        llm = LLMFactory.get_adapter(provider="groq", use_smart=True)
        print(f"[OK] LLM Adapter criado: {type(llm).__name__}")
        
        # Teste simples
        test_response = await llm.generate_response("Responda apenas: OK")
        print(f"[OK] LLM respondeu: {test_response[:50]}...")
        
    except Exception as e:
        print(f"[ERRO] Excecao em LLMFactory: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Passo 3: Testar LLMInsightsService completo
    print("\n[3/3] Testando LLMInsightsService completo...")
    try:
        from app.services.llm_insights import LLMInsightsService
        
        insights = await LLMInsightsService.generate_proactive_insights()
        
        if len(insights) > 0 and insights[0].get('title') == "Sistema de Insights em Manutencao":
            print(f"[ERRO] Retornou fallback!")
            print(f"       Descricao: {insights[0].get('description')}")
            return False
        else:
            print(f"[OK] {len(insights)} insights gerados com sucesso!")
            for i, insight in enumerate(insights[:2], 1):
                print(f"\n     {i}. {insight.get('title')}")
                print(f"        {insight.get('description')[:80]}...")
            return True
            
    except Exception as e:
        print(f"[ERRO] Excecao em LLMInsightsService: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_step_by_step())
    
    print("\n" + "="*50)
    if success:
        print("RESULTADO: SUCESSO - Sistema funcionando!")
    else:
        print("RESULTADO: FALHA - Verifique os erros acima")
    print("="*50 + "\n")
