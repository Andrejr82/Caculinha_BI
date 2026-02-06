"""
Teste de validacao: Graficos vs Textos
Valida que o agente retorna o tipo correto baseado na solicitacao
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from app.core.llm_gemini_adapter import GeminiLLMAdapter
from app.core.utils.field_mapper import FieldMapper
from app.core.agents.code_gen_agent import CodeGenAgent
from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test():
    logger.info("\n" + "="*80)
    logger.info("TESTE: Graficos vs Textos - Priorizacao Inteligente")
    logger.info("="*80 + "\n")

    llm = GeminiLLMAdapter(
        model_name=settings.LLM_MODEL_NAME,
        gemini_api_key=settings.GEMINI_API_KEY
    )

    field_mapper = FieldMapper()
    code_gen_agent = CodeGenAgent(llm=llm, field_mapper=field_mapper, query_retriever=None, pattern_matcher=None, response_cache=None, query_history=None)

    agent = CaculinhaBIAgent(llm=llm, code_gen_agent=code_gen_agent, field_mapper=field_mapper, enable_rag=False)

    tests = [
        {"query": "gere um grafico de vendas por segmento", "expected": "code_result", "desc": "Grafico explícito"},
        {"query": "analise o grupo oxford e me aponte as criticas", "expected": "text", "desc": "Analise textual"},
        {"query": "gere um relatorio de vendas", "expected": "text", "desc": "Relatorio textual"},
        {"query": "mostre um grafico de estoque por categoria", "expected": "code_result", "desc": "Grafico explícito 2"},
    ]

    results = []
    for test in tests:
        logger.info(f"\n[TEST] {test['desc']}: {test['query']}")
        logger.info(f"Esperado: {test['expected']}")

        result = await agent.run_async(user_query=test['query'], chat_history=[])
        actual = result.get('type', 'unknown')

        status = "PASS" if actual == test['expected'] else "FAIL"
        logger.info(f"[{status}] Recebido: {actual}")

        results.append({"desc": test['desc'], "expected": test['expected'], "actual": actual, "status": status})
        await asyncio.sleep(1)

    logger.info("\n" + "="*80)
    logger.info("RESUMO")
    logger.info("="*80)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len(results)
    logger.info(f"Passou: {passed}/{total} ({passed/total*100:.1f}%)")

    for r in results:
        icon = "OK" if r['status'] == 'PASS' else "X"
        logger.info(f"  [{icon}] {r['desc']}: {r['expected']} -> {r['actual']}")

    if passed == total:
        logger.info("\nSUCESSO TOTAL!")
    else:
        logger.warning("\nALGUNS TESTES FALHARAM")

if __name__ == "__main__":
    asyncio.run(test())
