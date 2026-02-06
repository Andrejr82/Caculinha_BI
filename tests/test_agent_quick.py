"""
Teste rapido do agente - Valida correcao do erro "Maximum conversation turns exceeded"
Foca na query problematica original: "analise o grupo oxford e me aponte as criticas"
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from app.core.llm_gemini_adapter import GeminiLLMAdapter
from app.core.utils.field_mapper import FieldMapper
from app.core.agents.code_gen_agent import CodeGenAgent
from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_oxford_analysis():
    """
    Testa a query original que estava falhando
    """
    logger.info("\n" + "="*80)
    logger.info("TESTE: Correcao do erro 'Maximum conversation turns exceeded'")
    logger.info("="*80 + "\n")

    # Initialize agent
    logger.info("Inicializando agente...")
    llm = GeminiLLMAdapter(
        model_name=settings.LLM_MODEL_NAME,
        gemini_api_key=settings.GEMINI_API_KEY
    )

    field_mapper = FieldMapper()
    code_gen_agent = CodeGenAgent(
        llm=llm,
        field_mapper=field_mapper,
        query_retriever=None,
        pattern_matcher=None,
        response_cache=None,
        query_history=None
    )

    agent = CaculinhaBIAgent(
        llm=llm,
        code_gen_agent=code_gen_agent,
        field_mapper=field_mapper,
        enable_rag=False
    )

    logger.info("Agente inicializado!\n")

    # Test queries
    test_queries = [
        "analise o grupo oxford e me aponte as criticas",
        "gere um relatorio de vendas do segmento ARMARINHO",
        "diagnostico da une 1685",
        "quais os produtos com maior margem",
    ]

    results = []

    for query in test_queries:
        logger.info(f"\n{'='*80}")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*80}")

        start_time = datetime.now()

        try:
            result = await agent.run_async(user_query=query, chat_history=[])
            elapsed = (datetime.now() - start_time).total_seconds()

            has_error = 'Maximum conversation turns exceeded' in str(result)
            status = "FAIL" if has_error else "PASS"

            logger.info(f"\n[{status}] Tempo: {elapsed:.2f}s")
            logger.info(f"Tipo: {result.get('type', 'unknown')}")

            if has_error:
                logger.error(f"ERRO DETECTADO: {result}")
            else:
                result_preview = str(result.get('result', ''))[:300]
                logger.info(f"Resultado: {result_preview}...")

            results.append({
                "query": query,
                "status": status,
                "elapsed": elapsed,
                "has_error": has_error
            })

        except Exception as e:
            logger.error(f"EXCEPTION: {e}", exc_info=True)
            results.append({
                "query": query,
                "status": "EXCEPTION",
                "elapsed": (datetime.now() - start_time).total_seconds(),
                "has_error": True,
                "error": str(e)
            })

        # Delay between queries
        await asyncio.sleep(2)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*80)

    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)

    logger.info(f"\nTotal: {total}")
    logger.info(f"Passou: {passed}/{total} ({passed/total*100:.1f}%)")
    logger.info(f"Falhou: {total-passed}/{total} ({(total-passed)/total*100:.1f}%)")

    for r in results:
        status_icon = "OK" if r['status'] == 'PASS' else "ERRO"
        logger.info(f"  [{status_icon}] {r['query']} ({r['elapsed']:.2f}s)")

    if passed == total:
        logger.info("\nTODOS OS TESTES PASSARAM! Correcao bem-sucedida.")
    else:
        logger.warning("\nALGUNS TESTES FALHARAM. Investigacao necessaria.")

    logger.info("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_oxford_analysis())
