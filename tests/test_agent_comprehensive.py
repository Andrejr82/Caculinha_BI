"""
Testes abrangentes do agente BI - Validacao de diferentes tipos de consultas
Testa: Graficos, Analises Criticas, Relatorios, Consultas Comerciais, Perguntas sobre Produtos
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test queries categorized by type
TEST_QUERIES = {
    "graficos": [
        "gere um grafico de vendas por segmento",
        "mostre um grafico de estoque por categoria no segmento ARMARINHO",
        "crie um grafico dos top 10 produtos mais vendidos",
    ],
    "analises_criticas": [
        "analise o grupo oxford e me aponte as criticas",
        "quais os problemas do segmento TECIDOS",
        "diagnostico da une 1685",
        "o que devo fazer para melhorar o desempenho da categoria LINHA COSTURA",
    ],
    "relatorios": [
        "gere um relatorio de vendas e rupturas do segmento ARMARINHO",
        "relatorio executivo da une 1685",
        "relatório de performance do fabricante CIRCULO",
    ],
    "consultas_comerciais": [
        "quais os produtos com maior margem de contribuicao",
        "produtos com ruptura critica na une 1685",
        "top 5 segmentos com maior volume de vendas",
        "estoque disponivel de produtos da categoria AVIAMENTOS",
    ],
    "produtos_individuais": [
        "analise o produto 369946",
        "mostre dados do produto TNT",
        "desempenho de vendas do produto 123456",
    ],
    "consultas_simples": [
        "quantas unes existem",
        "quais segmentos estao disponiveis",
        "total de produtos cadastrados",
    ]
}

async def test_query(agent: CaculinhaBIAgent, query: str, category: str) -> dict:
    """
    Testa uma query individual e retorna resultado
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"[{category.upper()}] Testando: {query}")
    logger.info(f"{'='*80}")

    start_time = datetime.now()

    try:
        result = await agent.run_async(user_query=query, chat_history=[])
        elapsed = (datetime.now() - start_time).total_seconds()

        result_type = result.get('type', 'unknown')
        has_error = 'error' in str(result).lower() or 'Maximum conversation turns exceeded' in str(result)

        status = "FAIL" if has_error else "PASS"

        logger.info(f"[{status}] Resultado: type={result_type}, tempo={elapsed:.2f}s")

        if has_error:
            logger.error(f"ERRO DETECTADO: {result}")
        else:
            # Log resumido do resultado
            if result_type == "code_result":
                chart_spec = result.get('chart_spec')
                if chart_spec:
                    logger.info(f"Grafico gerado com sucesso")
            elif result_type == "text":
                text_preview = str(result.get('result', ''))[:200]
                logger.info(f"Texto gerado: {text_preview}...")

        return {
            "query": query,
            "category": category,
            "status": status,
            "result_type": result_type,
            "elapsed_time": elapsed,
            "has_error": has_error,
            "result": result
        }

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"[EXCEPTION] {e}", exc_info=True)
        return {
            "query": query,
            "category": category,
            "status": "EXCEPTION",
            "result_type": "exception",
            "elapsed_time": elapsed,
            "has_error": True,
            "error": str(e)
        }

async def run_comprehensive_tests():
    """
    Executa bateria completa de testes
    """
    logger.info("\n" + "="*80)
    logger.info("INICIANDO TESTES ABRANGENTES DO AGENTE BI")
    logger.info("="*80 + "\n")

    # Initialize agent
    logger.info("Inicializando agente...")
    llm = GeminiLLMAdapter(
        model_name=settings.LLM_MODEL_NAME,
        gemini_api_key=settings.GEMINI_API_KEY,
        system_instruction="Voce e um assistente BI"
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
        enable_rag=False  # Desabilitar RAG para testes mais rapidos
    )

    logger.info("Agente inicializado com sucesso!\n")

    # Run tests for each category
    all_results = []

    for category, queries in TEST_QUERIES.items():
        logger.info(f"\n{'#'*80}")
        logger.info(f"CATEGORIA: {category.upper()} ({len(queries)} queries)")
        logger.info(f"{'#'*80}\n")

        for query in queries:
            result = await test_query(agent, query, category)
            all_results.append(result)

            # Small delay between queries to avoid rate limiting
            await asyncio.sleep(2)

    # Generate summary report
    logger.info("\n" + "="*80)
    logger.info("RELATORIO FINAL DE TESTES")
    logger.info("="*80 + "\n")

    total_tests = len(all_results)
    passed = sum(1 for r in all_results if r['status'] == 'PASS')
    failed = sum(1 for r in all_results if r['status'] == 'FAIL')
    exceptions = sum(1 for r in all_results if r['status'] == 'EXCEPTION')

    logger.info(f"Total de testes: {total_tests}")
    logger.info(f"Passou: {passed} ({passed/total_tests*100:.1f}%)")
    logger.info(f"Falhou: {failed} ({failed/total_tests*100:.1f}%)")
    logger.info(f"Excecoes: {exceptions} ({exceptions/total_tests*100:.1f}%)")

    # Summary by category
    logger.info("\n" + "-"*80)
    logger.info("RESUMO POR CATEGORIA")
    logger.info("-"*80)

    for category in TEST_QUERIES.keys():
        category_results = [r for r in all_results if r['category'] == category]
        cat_passed = sum(1 for r in category_results if r['status'] == 'PASS')
        cat_total = len(category_results)
        logger.info(f"{category}: {cat_passed}/{cat_total} ({cat_passed/cat_total*100:.1f}%)")

    # Failed tests detail
    failed_results = [r for r in all_results if r['status'] != 'PASS']
    if failed_results:
        logger.info("\n" + "-"*80)
        logger.info("TESTES COM FALHA")
        logger.info("-"*80)
        for r in failed_results:
            logger.info(f"[{r['category']}] {r['query']}")
            if 'error' in r:
                logger.info(f"  Erro: {r['error']}")
            else:
                logger.info(f"  Resultado: {str(r.get('result', ''))[:200]}")

    # Performance stats
    avg_time = sum(r['elapsed_time'] for r in all_results) / total_tests
    max_time = max(r['elapsed_time'] for r in all_results)
    min_time = min(r['elapsed_time'] for r in all_results)

    logger.info("\n" + "-"*80)
    logger.info("ESTATISTICAS DE PERFORMANCE")
    logger.info("-"*80)
    logger.info(f"Tempo medio: {avg_time:.2f}s")
    logger.info(f"Tempo minimo: {min_time:.2f}s")
    logger.info(f"Tempo maximo: {max_time:.2f}s")

    logger.info("\n" + "="*80)
    logger.info("TESTES CONCLUIDOS")
    logger.info("="*80 + "\n")

    return all_results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
