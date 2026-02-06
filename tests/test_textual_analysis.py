"""
Teste de validacao da resposta textual para analises criticas
Valida se o agente retorna analise textual (nao grafico) para queries de diagnostico
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

async def test_textual_analysis():
    """
    Testa se a query original agora retorna analise textual (nao grafico)
    """
    logger.info("\n" + "="*80)
    logger.info("TESTE: Validacao de Resposta Textual para Analises Criticas")
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

    # Test queries que DEVEM retornar texto (nao grafico)
    test_queries = [
        {
            "query": "analise o grupo oxford e me aponte as criticas a serem corrigidas com o que devo fazer",
            "expected_type": "text",
            "description": "Query original do usuario"
        },
        {
            "query": "diagnostico da une 1685",
            "expected_type": "text",
            "description": "Diagnostico de loja"
        },
        {
            "query": "gere um relatorio executivo do segmento ARMARINHO",
            "expected_type": "text",
            "description": "Relatorio executivo"
        },
        {
            "query": "o que devo fazer para melhorar as vendas da categoria TECIDOS",
            "expected_type": "text",
            "description": "Recomendacoes de acao"
        }
    ]

    results = []

    for test_case in test_queries:
        query = test_case["query"]
        expected_type = test_case["expected_type"]
        description = test_case["description"]

        logger.info(f"\n{'='*80}")
        logger.info(f"Teste: {description}")
        logger.info(f"Query: {query}")
        logger.info(f"Tipo esperado: {expected_type}")
        logger.info(f"{'='*80}")

        start_time = datetime.now()

        try:
            result = await agent.run_async(user_query=query, chat_history=[])
            elapsed = (datetime.now() - start_time).total_seconds()

            result_type = result.get('type', 'unknown')

            # Validar se retornou o tipo correto
            is_correct_type = result_type == expected_type

            # Validar se tem conteudo textual substantivo (nao apenas "Aqui esta o grafico")
            result_content = str(result.get('result', ''))
            has_substantial_text = len(result_content) > 100  # Pelo menos 100 chars

            # Validar se tem estrutura de analise (markdown headers)
            has_structure = '**' in result_content or '##' in result_content

            # Status final
            if is_correct_type and has_substantial_text and has_structure:
                status = "PASS"
                logger.info(f"[PASS] Tipo correto ({result_type}), texto substantivo ({len(result_content)} chars), estruturado")
            elif is_correct_type and has_substantial_text:
                status = "PARTIAL"
                logger.warning(f"[PARTIAL] Tipo correto mas falta estruturacao")
            elif is_correct_type:
                status = "PARTIAL"
                logger.warning(f"[PARTIAL] Tipo correto mas texto muito curto ({len(result_content)} chars)")
            else:
                status = "FAIL"
                logger.error(f"[FAIL] Tipo incorreto: esperado {expected_type}, recebido {result_type}")

            # Log preview do conteudo
            content_preview = result_content[:300]
            logger.info(f"Preview: {content_preview}...")
            logger.info(f"Tempo: {elapsed:.2f}s\n")

            results.append({
                "description": description,
                "query": query,
                "expected_type": expected_type,
                "actual_type": result_type,
                "status": status,
                "elapsed": elapsed,
                "content_length": len(result_content),
                "has_structure": has_structure
            })

        except Exception as e:
            logger.error(f"[EXCEPTION] {e}", exc_info=True)
            results.append({
                "description": description,
                "query": query,
                "expected_type": expected_type,
                "actual_type": "exception",
                "status": "FAIL",
                "elapsed": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
            })

        # Delay entre queries
        await asyncio.sleep(2)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*80)

    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    partial = sum(1 for r in results if r['status'] == 'PARTIAL')
    failed = sum(1 for r in results if r['status'] == 'FAIL')

    logger.info(f"\nTotal: {total}")
    logger.info(f"Passou: {passed}/{total} ({passed/total*100:.1f}%)")
    logger.info(f"Parcial: {partial}/{total} ({partial/total*100:.1f}%)")
    logger.info(f"Falhou: {failed}/{total} ({failed/total*100:.1f}%)")

    logger.info("\n" + "-"*80)
    logger.info("DETALHES")
    logger.info("-"*80)

    for r in results:
        status_icon = "OK" if r['status'] == 'PASS' else ("~" if r['status'] == 'PARTIAL' else "X")
        type_info = f"{r['expected_type']} -> {r['actual_type']}"
        logger.info(f"  [{status_icon}] {r['description']}: {type_info} ({r['elapsed']:.2f}s)")

    if passed == total:
        logger.info("\nSUCESSO TOTAL! Todas as queries retornaram analise textual correta.")
    elif passed + partial == total:
        logger.info("\nSUCESSO PARCIAL. Todas retornaram texto, mas algumas precisam melhorar estruturacao.")
    else:
        logger.warning("\nALGUNS TESTES FALHARAM. Ainda ha queries retornando graficos ao inves de texto.")

    logger.info("\n" + "="*80 + "\n")

    return results

if __name__ == "__main__":
    asyncio.run(test_textual_analysis())
