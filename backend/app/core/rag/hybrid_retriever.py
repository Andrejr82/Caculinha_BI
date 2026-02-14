"""
Hybrid Retriever - BM25 + Dense Embeddings (2025)
==================================================

Implementa retrieval híbrido moderno combinando:
- BM25 (keyword-based) para queries com termos específicos (códigos, nomes exatos)
- Dense Embeddings (semantic) para queries conceituais

Baseado em best practices 2025: +12-30% acurácia vs. métodos isolados.

Author: Agent BI Team
Date: 2025-12-27
"""

import os
import json
import logging
import functools
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

import polars as pl

from backend.app.config.settings import settings
from backend.app.core.rag.example_collector import ExampleCollector

logger = logging.getLogger(__name__)

# Lazy imports para otimizar cold start
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    logger.warning("rank_bm25 não instalado. BM25 retrieval não disponível. Install: pip install rank-bm25")
    HAS_BM25 = False

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    logger.warning("google-genai não instalado. Embeddings não disponíveis.")
    HAS_GEMINI = False


class HybridRetriever:
    """
    Retriever híbrido que combina BM25 e Dense Embeddings.

    Estratégia de fusão: Reciprocal Rank Fusion (RRF)
    - RRF combina rankings de diferentes métodos de forma robusta
    - Não requer normalização de scores
    - Usado em produção por Cohere, Weaviate, etc.
    """

    def __init__(
        self,
        examples_path: str = None,
        embedding_model: str = "models/text-embedding-004",
        bm25_weight: float = 0.5,
        dense_weight: float = 0.5,
        use_cache: bool = True
    ):
        """
        Inicializa o Hybrid Retriever.

        Args:
            examples_path: Caminho para exemplos/documentos
            embedding_model: Modelo de embedding (text-embedding-004 = Google 2024)
            bm25_weight: Peso do BM25 no ranking final (0.0-1.0)
            dense_weight: Peso do dense embeddings (0.0-1.0)
            use_cache: Se True, cacheia embeddings
        """
        self.examples_path = examples_path or settings.LEARNING_EXAMPLES_PATH
        self.embedding_model_name = embedding_model
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.use_cache = use_cache

        # Caminhos
        self.embeddings_cache_path = Path(self.examples_path) / "embeddings_cache.json"
        self.bm25_index_path = Path(self.examples_path) / "bm25_index.json"

        # Componentes
        self.example_collector = ExampleCollector(examples_dir=self.examples_path)
        self.bm25_index: Optional[BM25Okapi] = None
        self.embeddings_cache: Dict[str, List[float]] = {}
        self.documents: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []

        # Embedding model (Gemini)
        self.embedding_model = None

        # Lazy initialization flags
        self._initialized = False
        self._warming = False  # NEW 2025-12-27: Background warming in progress
        self._lock = asyncio.Lock()  # NEW 2025-12-27: Async lock for thread safety

        logger.info(f"HybridRetriever criado (BM25={bm25_weight}, Dense={dense_weight})")

    def _ensure_initialized(self) -> bool:
        """
        Lazy initialization: carrega índices apenas quando necessário.
        """
        if self._initialized:
            return True

        try:
            logger.info("Inicializando HybridRetriever...")

            # 1. Carregar documentos
            self.documents = self.example_collector.get_all_examples()

            if not self.documents:
                logger.warning("Nenhum documento encontrado para indexação")
                return False

            logger.info(f"Carregados {len(self.documents)} documentos")

            # 2. Inicializar Gemini Embeddings
            if HAS_GEMINI and settings.GEMINI_API_KEY:
                try:
                    self.embedding_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    logger.info(f"Gemini Client configurado para embeddings: {self.embedding_model_name}")
                except Exception as e:
                    logger.error(f"Erro ao configurar Gemini Client: {e}")
                    return False
            else:
                logger.warning("Gemini não disponível. Dense retrieval desabilitado.")

            # 3. Inicializar BM25
            if HAS_BM25:
                self._initialize_bm25()
            else:
                logger.warning("BM25 não disponível")

            # 4. Carregar/gerar embeddings
            if HAS_GEMINI:
                self._load_or_generate_embeddings()

            self._initialized = True
            logger.info("HybridRetriever inicializado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar HybridRetriever: {e}", exc_info=True)
            return False

    def _initialize_bm25(self) -> None:
        """
        Inicializa o índice BM25.
        """
        try:
            logger.info("Indexando documentos com BM25...")

            # Tokenizar corpus
            self.tokenized_corpus = [
                self._tokenize(doc.get('query', ''))
                for doc in self.documents
            ]

            # Criar índice BM25
            self.bm25_index = BM25Okapi(self.tokenized_corpus)

            logger.info(f"BM25 index criado com {len(self.tokenized_corpus)} documentos")

        except Exception as e:
            logger.error(f"Erro ao inicializar BM25: {e}")

    def _load_or_generate_embeddings(self) -> None:
        """
        Carrega embeddings do cache ou gera novos.
        """
        try:
            # Tentar carregar cache
            if self.use_cache and self.embeddings_cache_path.exists():
                logger.info("Carregando embeddings do cache...")
                with open(self.embeddings_cache_path, 'r', encoding='utf-8') as f:
                    self.embeddings_cache = json.load(f)
                logger.info(f"Cache carregado: {len(self.embeddings_cache)} embeddings")

            # Gerar embeddings faltantes
            missing_docs = [
                doc for doc in self.documents
                if doc.get('query') not in self.embeddings_cache
            ]

            if missing_docs:
                logger.info(f"Gerando embeddings para {len(missing_docs)} novos documentos...")
                for doc in missing_docs:
                    query = doc.get('query', '')
                    if query:
                        embedding = self._generate_embedding(query)
                        if embedding:
                            self.embeddings_cache[query] = embedding

                # Salvar cache atualizado
                if self.use_cache:
                    self._save_embeddings_cache()

        except Exception as e:
            logger.error(f"Erro ao carregar/gerar embeddings: {e}")

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Gera embedding usando Gemini text-embedding-004.

        Args:
            text: Texto para gerar embedding

        Returns:
            Lista de floats representando o embedding, ou None se falhar
        """
        try:
            # New SDK v1 syntax
            result = self.embedding_client.models.embed_content(
                model=self.embedding_model_name,
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            # Result object has 'embeddings' attribute which is a list of Embedding objects
            # We assume single content, so we take the first one
            return result.embeddings[0].values

        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return None

    def _save_embeddings_cache(self) -> None:
        """
        Salva cache de embeddings em disco.
        """
        try:
            with open(self.embeddings_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.embeddings_cache, f, indent=2)
            logger.info(f"Cache de embeddings salvo: {len(self.embeddings_cache)} entries")
        except Exception as e:
            logger.error(f"Erro ao salvar cache de embeddings: {e}")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokeniza texto para BM25.

        Remove stopwords e normaliza.
        """
        # Stopwords básicas do português
        stopwords = {
            'o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos',
            'em', 'no', 'na', 'nos', 'nas', 'para', 'por', 'com',
            'sem', 'sob', 'sobre', 'e', 'ou', 'mas', 'que', 'qual',
            'quais', 'é', 'são', 'foi', 'foram', 'ser', 'estar'
        }

        # Tokenizar e limpar
        tokens = text.lower().split()
        tokens = [
            token.strip('.,!?;:()[]{}')
            for token in tokens
            if token.strip('.,!?;:()[]{}') not in stopwords
            and len(token) > 2
        ]

        return tokens

    def _bm25_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Busca usando BM25 (keyword-based).

        Args:
            query: Query de busca
            top_k: Número de resultados

        Returns:
            Lista de documentos com scores
        """
        if not HAS_BM25 or self.bm25_index is None:
            return []

        try:
            # Tokenizar query
            tokenized_query = self._tokenize(query)

            # Buscar
            scores = self.bm25_index.get_scores(tokenized_query)

            # Ranquear
            doc_scores = [
                {'doc': self.documents[i], 'score': scores[i], 'method': 'bm25'}
                for i in range(len(scores))
            ]
            doc_scores.sort(key=lambda x: x['score'], reverse=True)

            return doc_scores[:top_k]

        except Exception as e:
            logger.error(f"Erro no BM25 search: {e}")
            return []

    def _dense_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Busca usando dense embeddings (semantic).

        Args:
            query: Query de busca
            top_k: Número de resultados

        Returns:
            Lista de documentos com scores
        """
        if not HAS_GEMINI or not self.embeddings_cache:
            return []

        try:
            # Gerar embedding da query
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                return []

            # Calcular similaridade de cosseno com cada documento
            similarities = []
            for doc in self.documents:
                doc_query = doc.get('query', '')
                if doc_query in self.embeddings_cache:
                    doc_embedding = self.embeddings_cache[doc_query]
                    similarity = self._cosine_similarity(query_embedding, doc_embedding)
                    similarities.append({
                        'doc': doc,
                        'score': similarity,
                        'method': 'dense'
                    })

            # Ranquear
            similarities.sort(key=lambda x: x['score'], reverse=True)

            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Erro no dense search: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calcula similaridade de cosseno entre dois vetores.
        """
        try:
            import math

            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            return dot_product / (magnitude1 * magnitude2)

        except Exception as e:
            logger.error(f"Erro ao calcular cosine similarity: {e}")
            return 0.0

    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[Dict[str, Any]],
        dense_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Combina resultados usando Reciprocal Rank Fusion (RRF).

        RRF formula: RRF(d) = Σ 1/(k + rank(d))

        Args:
            bm25_results: Resultados do BM25
            dense_results: Resultados do dense search
            k: Constante RRF (padrão 60, usado em produção)

        Returns:
            Lista combinada e ranqueada
        """
        # Mapear documentos para RRF scores
        rrf_scores: Dict[str, Dict[str, Any]] = {}

        # Processar BM25 results
        for rank, result in enumerate(bm25_results):
            doc_id = result['doc'].get('query', '')
            if doc_id:
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = {
                        'doc': result['doc'],
                        'rrf_score': 0.0,
                        'bm25_rank': None,
                        'dense_rank': None,
                        'bm25_score': None,
                        'dense_score': None
                    }

                rrf_scores[doc_id]['rrf_score'] += self.bm25_weight / (k + rank + 1)
                rrf_scores[doc_id]['bm25_rank'] = rank + 1
                rrf_scores[doc_id]['bm25_score'] = result['score']

        # Processar Dense results
        for rank, result in enumerate(dense_results):
            doc_id = result['doc'].get('query', '')
            if doc_id:
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = {
                        'doc': result['doc'],
                        'rrf_score': 0.0,
                        'bm25_rank': None,
                        'dense_rank': None,
                        'bm25_score': None,
                        'dense_score': None
                    }

                rrf_scores[doc_id]['rrf_score'] += self.dense_weight / (k + rank + 1)
                rrf_scores[doc_id]['dense_rank'] = rank + 1
                rrf_scores[doc_id]['dense_score'] = result['score']

        # Converter para lista e ordenar por RRF score
        combined_results = list(rrf_scores.values())
        combined_results.sort(key=lambda x: x['rrf_score'], reverse=True)

        return combined_results

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        method: str = 'hybrid'
    ) -> List[Dict[str, Any]]:
        """
        Retrieval principal - combina BM25 e Dense.

        Args:
            query: Query de busca
            top_k: Número de resultados
            method: 'hybrid', 'bm25', ou 'dense'

        Returns:
            Lista de documentos ranqueados
        """
        # Lazy initialization
        if not self._ensure_initialized():
            logger.error("Falha ao inicializar HybridRetriever")
            return []

        try:
            if method == 'bm25':
                results = self._bm25_search(query, top_k)
                return [{'doc': r['doc'], 'score': r['score'], 'method': 'bm25'} for r in results]

            elif method == 'dense':
                results = self._dense_search(query, top_k)
                return [{'doc': r['doc'], 'score': r['score'], 'method': 'dense'} for r in results]

            else:  # hybrid (default)
                # Buscar com ambos os métodos (top_k * 2 para ter margem)
                bm25_results = self._bm25_search(query, top_k * 2)
                dense_results = self._dense_search(query, top_k * 2)

                # Combinar com RRF
                combined = self._reciprocal_rank_fusion(bm25_results, dense_results)

                # Retornar top_k
                return combined[:top_k]

        except Exception as e:
            logger.error(f"Erro no retrieve: {e}", exc_info=True)
            return []

    # ========================================================================
    # ASYNC METHODS - Modern Python 3.11+ asyncio patterns (2025-12-27)
    # ========================================================================

    async def start_background_warming(self) -> None:
        """
        Inicia warming em background sem bloquear.
        Seguro para chamar múltiplas vezes (usa lock).
        """
        async with self._lock:
            if self._initialized or self._warming:
                logger.info("[RAG] Já inicializado ou warming em progresso. Skipping.")
                return

            self._warming = True
            logger.info("[RAG] Iniciando background warming...")

        try:
            # Run blocking initialization in thread pool
            await asyncio.to_thread(self._ensure_initialized)
            logger.info("[RAG] Background warming concluído!")
        except Exception as e:
            logger.error(f"[RAG] Erro no background warming: {e}", exc_info=True)
        finally:
            async with self._lock:
                self._warming = False

    async def _generate_embedding_async(self, text: str) -> Optional[List[float]]:
        """
        Versão async de _generate_embedding.
        Executa em thread pool para não bloquear event loop.
        """
        try:
            # Wrapper function for the client call
            def _embed():
                res = self.embedding_client.models.embed_content(
                    model=self.embedding_model_name,
                    contents=text,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                return res.embeddings[0].values

            result = await asyncio.to_thread(_embed)
            return result
        except Exception as e:
            logger.error(f"[RAG] Erro ao gerar embedding async: {e}")
            return None

    async def retrieve_async(
        self,
        query: str,
        top_k: int = 5,
        method: str = 'hybrid',
        wait_if_warming: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Versão async de retrieve() - não bloqueia se não estiver pronto.

        Args:
            query: Query de busca
            top_k: Número de resultados
            method: 'hybrid', 'bm25', ou 'dense'
            wait_if_warming: Se True, aguarda warming terminar. Se False, retorna [] se não pronto.

        Returns:
            Lista de documentos ranqueados, ou [] se não pronto e wait_if_warming=False
        """
        # Check if ready
        if not self._initialized:
            if self._warming:
                if wait_if_warming:
                    logger.info("[RAG] Aguardando warming terminar...")
                    # Wait for warming with timeout
                    for _ in range(50):  # Max 10s wait (50 * 200ms)
                        await asyncio.sleep(0.2)
                        if self._initialized:
                            break

                    if not self._initialized:
                        logger.warning("[RAG] Timeout aguardando warming. Retornando []")
                        return []
                else:
                    logger.info("[RAG] Warming em progresso, mas wait_if_warming=False. Retornando []")
                    return []
            else:
                logger.warning("[RAG] Não inicializado e não está warming. Retornando []")
                return []

        # Use sync retrieve in thread pool
        try:
            results = await asyncio.to_thread(
                self.retrieve,
                query,
                top_k,
                method
            )
            return results
        except Exception as e:
            logger.error(f"[RAG] Erro no retrieve_async: {e}", exc_info=True)
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do retriever.
        """
        return {
            'initialized': self._initialized,
            'warming': self._warming,  # NEW 2025-12-27
            'total_documents': len(self.documents),
            'embeddings_cached': len(self.embeddings_cache),
            'bm25_available': HAS_BM25 and self.bm25_index is not None,
            'dense_available': HAS_GEMINI and bool(self.embeddings_cache),
            'embedding_model': self.embedding_model_name,
            'bm25_weight': self.bm25_weight,
            'dense_weight': self.dense_weight
        }


# Singleton instance
_hybrid_retriever: Optional[HybridRetriever] = None


def get_hybrid_retriever() -> HybridRetriever:
    """
    Retorna instância singleton do HybridRetriever.
    """
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever
