
import asyncio
import sys
import logging
from pprint import pprint

# Setup paths
import os
import sys
# Force reload of .env
from dotenv import load_dotenv
load_dotenv(override=True)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.llm_insights import LLMInsightsService
from app.core.data_source_manager import get_data_manager

# Configura logging para ver logs do serviço
logging.basicConfig(level=logging.INFO)

# Fix para Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

async def test_insights():
    print("--- 1. Testando Data Manager (Aggregacao) ---")
    try:
        from app.services.data_aggregation import DataAggregationService
        summary = DataAggregationService.get_retail_summary(limit_items=3)
        print("Summary keys:", summary.keys())
        print("Total Sales:", summary.get("general_stats", {}).get("total_sales_30d"))
    except Exception as e:
        print(f"Erro no Aggregation: {e}")
        return

    print("\n--- 2. Testando Geração de Insights com LLM ---")
    try:
        insights = await LLMInsightsService.generate_proactive_insights()
        print(f"Insights gerados: {len(insights)}")
        
        # Check fallback
        if len(insights) == 1 and insights[0].get("title") == "Sistema de Insights em Manutenção":
            print("❌ FALLBACK DETECTADO! O sistema falhou em gerar insights reais.")
            print(f"Detalhes do erro: {insights[0].get('description')}")
        else:
            print(f"✅ SUCESSO! {len(insights)} insights gerados.")
            for i, ins in enumerate(insights):
                print(f"\n--- Insight {i+1} ---")
                pprint(ins)
                # Validação
                if not ins.get("title"):
                    print("⚠️  AVISO: Título vazio ou chave incorreta.")

    except Exception as e:
        print(f"Erro fatal no script: {e}")

if __name__ == "__main__":
    asyncio.run(test_insights())
