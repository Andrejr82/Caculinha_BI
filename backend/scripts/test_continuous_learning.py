"""
Script de Teste - Sistema de Continuous Learning
=================================================

Testa todos os componentes do sistema de aprendizado contínuo:
- ContinuousLearner
- HybridRetriever
- ConfidenceScorer

Execute: python scripts/test_continuous_learning.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.learning.continuous_learner import get_continuous_learner
from backend.app.core.rag.hybrid_retriever import get_hybrid_retriever
from backend.app.core.utils.confidence_scorer import get_confidence_scorer


def print_section(title: str):
    """Helper para imprimir seções."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


async def test_confidence_scorer():
    """Testa o ConfidenceScorer."""
    print_section("Teste 1: Confidence Scorer")

    scorer = get_confidence_scorer()

    # Teste 1: Resposta de alta qualidade
    response_high = """
    Aqui estão os top 10 produtos mais vendidos:

    1. Produto A - 1.250 vendas
    2. Produto B - 1.100 vendas
    3. Produto C - 980 vendas
    ...
    """

    confidence_high = scorer.calculate_confidence(
        response=response_high,
        rag_similarity=0.92,
        tool_results=[{'status': 'success', 'data': [1, 2, 3]}],
        query_length=25
    )

    print(f"\n[+] Resposta de alta qualidade:")
    print(f"   Confidence: {confidence_high:.2f}")
    print(f"   Label: {scorer.get_confidence_label(confidence_high)}")
    print(f"   Route to human: {scorer.should_route_to_human(confidence_high)}")

    # Teste 2: Resposta de baixa qualidade
    response_low = "Desculpe, nao consegui processar sua solicitacao."

    confidence_low = scorer.calculate_confidence(
        response=response_low,
        rag_similarity=0.3,
        tool_results=[{'status': 'error', 'error': 'Failed'}],
        query_length=50
    )

    print(f"\n[-] Resposta de baixa qualidade:")
    print(f"   Confidence: {confidence_low:.2f}")
    print(f"   Label: {scorer.get_confidence_label(confidence_low)}")
    print(f"   Route to human: {scorer.should_route_to_human(confidence_low)}")


async def test_continuous_learner():
    """Testa o ContinuousLearner."""
    print_section("Teste 2: Continuous Learner")

    learner = get_continuous_learner()

    # Teste 1: Feedback positivo
    print("\n[*] Processando feedback positivo...")
    result_positive = await learner.process_interaction(
        query="Quais os top 10 produtos mais vendidos?",
        response={"type": "text", "content": "Aqui estao os top 10..."},
        feedback_type="positive",
        user_comment="Excelente resposta!",
        confidence_score=0.92,
        session_id="test-session-1",
        user_id="test-user-1"
    )

    print(f"   Actions taken: {result_positive['actions_taken']}")
    print(f"   Stats: Positive={result_positive['stats']['positive_count']}")

    # Teste 2: Feedback negativo
    print("\n[*] Processando feedback negativo...")
    result_negative = await learner.process_interaction(
        query="Vendas da UNE 999",
        response={"type": "error", "content": "UNE nao encontrada"},
        feedback_type="negative",
        user_comment="UNE nao existe no sistema",
        confidence_score=0.45,
        session_id="test-session-2",
        user_id="test-user-2"
    )

    print(f"   Actions taken: {result_negative['actions_taken']}")
    print(f"   Recommendations: {result_negative['recommendations']}")

    # Teste 3: Low confidence (sem feedback ainda)
    print("\n[*] Processando low confidence...")
    result_low_conf = await learner.process_interaction(
        query="Como calcular o giro de estoque?",
        response={"type": "text", "content": "Talvez voce possa..."},
        feedback_type=None,
        confidence_score=0.55,
        session_id="test-session-3",
        user_id="test-user-3"
    )

    print(f"   Actions taken: {result_low_conf['actions_taken']}")

    # Stats do Golden Dataset
    print("\n[i] Estatisticas do Golden Dataset:")
    stats = learner.get_golden_dataset_stats()
    print(f"   Golden examples: {stats['golden_examples']}")
    print(f"   Pending review: {stats['pending_review']}")
    print(f"   Buffer size: {stats['buffer_size']}")

    # Pending reviews
    print("\n[i] Itens pendentes de review:")
    reviews = learner.get_pending_reviews(limit=5)
    for i, review in enumerate(reviews, 1):
        print(f"   {i}. [{review.get('priority', 'N/A')}] {review.get('query', 'N/A')[:50]}...")


async def test_hybrid_retriever():
    """Testa o HybridRetriever."""
    print_section("Teste 3: Hybrid Retriever")

    retriever = get_hybrid_retriever()

    # Stats
    print("\n[i] Estatisticas do Retriever:")
    stats = retriever.get_stats()
    print(f"   Initialized: {stats['initialized']}")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Embeddings cached: {stats['embeddings_cached']}")
    print(f"   BM25 available: {stats['bm25_available']}")
    print(f"   Dense available: {stats['dense_available']}")
    print(f"   Model: {stats['embedding_model']}")

    # Se nao houver documentos, adicionar alguns exemplos
    if stats['total_documents'] == 0:
        print("\n[!] Nenhum documento encontrado. Adicione exemplos em data/learning/")
        print("   Exemplo: Copie arquivos do golden_dataset para data/learning/")
        return

    # Teste de retrieval
    test_queries = [
        "vendas por segmento",
        "produtos em ruptura",
        "transferencias entre UNEs",
        "top 10 produtos mais vendidos"
    ]

    for query in test_queries:
        print(f"\n[?] Query: '{query}'")

        # Hybrid
        results_hybrid = retriever.retrieve(query, top_k=3, method='hybrid')
        print(f"   Hybrid: {len(results_hybrid)} resultados")
        if results_hybrid:
            print(f"   Top result: {results_hybrid[0]['doc'].get('query', 'N/A')[:60]}...")
            print(f"   RRF Score: {results_hybrid[0].get('rrf_score', 0):.4f}")

        # BM25 only
        if stats['bm25_available']:
            results_bm25 = retriever.retrieve(query, top_k=3, method='bm25')
            print(f"   BM25: {len(results_bm25)} resultados")

        # Dense only
        if stats['dense_available']:
            results_dense = retriever.retrieve(query, top_k=3, method='dense')
            print(f"   Dense: {len(results_dense)} resultados")


async def main():
    """Main test runner."""
    print("\n" + "="*60)
    print(" TESTE DO SISTEMA DE CONTINUOUS LEARNING")
    print("="*60)

    try:
        # Teste 1: ConfidenceScorer
        await test_confidence_scorer()

        # Teste 2: ContinuousLearner
        await test_continuous_learner()

        # Teste 3: HybridRetriever
        await test_hybrid_retriever()

        print_section("[+] TODOS OS TESTES CONCLUIDOS")
        print("\n[*] Proximos passos:")
        print("   1. Verificar diretorios criados em data/learning/golden_dataset/")
        print("   2. Revisar logs em logs/backend.log")
        print("   3. Testar endpoints via API:")
        print("      - GET /api/v1/learning/golden-dataset-stats")
        print("      - GET /api/v1/learning/hybrid-retriever-stats")
        print("      - POST /api/v1/learning/submit-feedback")
        print("\n[i] Documentacao completa:")
        print("   - backend/CONTINUOUS_LEARNING_GUIDE.md")
        print("   - backend/CLAUDE.md (atualizado)\n")

    except Exception as e:
        print(f"\n[-] ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
