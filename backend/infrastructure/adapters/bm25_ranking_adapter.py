"""
BM25RankingAdapter — Adapter de Ranking BM25

Implementação de ranking usando BM25 (sparse retrieval).

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import math
from typing import List, Tuple, Dict
from collections import defaultdict
import re

import structlog

from backend.domain.ports.ranking_port import IRankingPort, RankedDocument
from backend.domain.entities.document import Document


logger = structlog.get_logger(__name__)


class BM25RankingAdapter(IRankingPort):
    """
    Adapter BM25 para ranking de documentos.
    
    Implementa BM25 (Best Matching 25) para ranking sparse.
    Ideal para: busca por palavras-chave, ranking inicial.
    """
    
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        """
        Inicializa o adapter BM25.
        
        Args:
            k1: Parâmetro de saturação de termo
            b: Parâmetro de normalização por tamanho
            epsilon: Epsilon para evitar divisão por zero
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza texto em palavras."""
        # Remove pontuação e converte para minúsculas
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Remove stopwords básicas
        stopwords = {'a', 'o', 'e', 'de', 'da', 'do', 'em', 'para', 'com', 'que', 'the', 'is', 'at', 'on', 'in'}
        return [t for t in tokens if t not in stopwords and len(t) > 1]
    
    def _compute_idf(self, documents: List[Document]) -> Dict[str, float]:
        """Calcula IDF para cada termo."""
        n_docs = len(documents)
        doc_freq = defaultdict(int)
        
        for doc in documents:
            tokens = set(self._tokenize(doc.content))
            for token in tokens:
                doc_freq[token] += 1
        
        idf = {}
        for term, freq in doc_freq.items():
            idf[term] = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1)
        
        return idf
    
    def _compute_bm25_score(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        avg_doc_len: float,
        idf: Dict[str, float],
    ) -> float:
        """Calcula score BM25 para um documento."""
        doc_len = len(doc_tokens)
        term_freq = defaultdict(int)
        
        for token in doc_tokens:
            term_freq[token] += 1
        
        score = 0.0
        for token in query_tokens:
            if token in idf:
                tf = term_freq.get(token, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len)
                score += idf[token] * numerator / (denominator + self.epsilon)
        
        return score
    
    async def rank_bm25(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 10,
    ) -> List[RankedDocument]:
        """Ranking usando BM25."""
        if not documents:
            return []
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        # Tokeniza todos os documentos
        doc_tokens_list = [self._tokenize(doc.content) for doc in documents]
        avg_doc_len = sum(len(tokens) for tokens in doc_tokens_list) / len(documents)
        
        # Calcula IDF
        idf = self._compute_idf(documents)
        
        # Calcula scores
        scored_docs = []
        for doc, doc_tokens in zip(documents, doc_tokens_list):
            score = self._compute_bm25_score(query_tokens, doc_tokens, avg_doc_len, idf)
            scored_docs.append((doc, score))
        
        # Ordena por score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Retorna top_k
        return [
            RankedDocument(
                document=doc,
                score=score,
                rank=i + 1,
                method="bm25",
            )
            for i, (doc, score) in enumerate(scored_docs[:top_k])
        ]
    
    async def rank_neural(
        self,
        query_embedding: List[float],
        documents: List[Tuple[Document, List[float]]],
        top_k: int = 10,
    ) -> List[RankedDocument]:
        """Ranking usando similaridade neural."""
        if not documents:
            return []
        
        # Calcula similaridade de cosseno
        scored_docs = []
        for doc, doc_embedding in documents:
            score = self._cosine_similarity(query_embedding, doc_embedding)
            scored_docs.append((doc, score))
        
        # Ordena por score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [
            RankedDocument(
                document=doc,
                score=score,
                rank=i + 1,
                method="neural",
            )
            for i, (doc, score) in enumerate(scored_docs[:top_k])
        ]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def rank_hybrid(
        self,
        query: str,
        query_embedding: List[float],
        documents: List[Tuple[Document, List[float]]],
        top_k: int = 10,
        alpha: float = 0.5,
    ) -> List[RankedDocument]:
        """Ranking híbrido combinando BM25 e neural."""
        if not documents:
            return []
        
        # Separa documentos e embeddings
        docs = [doc for doc, _ in documents]
        
        # Ranking BM25
        bm25_results = await self.rank_bm25(query, docs, top_k=len(docs))
        
        # Ranking Neural
        neural_results = await self.rank_neural(query_embedding, documents, top_k=len(docs))
        
        # Combina com RRF
        return await self.reciprocal_rank_fusion(
            [bm25_results, neural_results],
            top_k=top_k,
        )
    
    async def reciprocal_rank_fusion(
        self,
        rankings: List[List[RankedDocument]],
        k: int = 60,
        top_k: int = 10,
    ) -> List[RankedDocument]:
        """Combina múltiplos rankings usando RRF."""
        scores = defaultdict(float)
        docs = {}
        
        for ranking in rankings:
            for ranked_doc in ranking:
                doc_id = ranked_doc.document.id
                scores[doc_id] += 1 / (k + ranked_doc.rank)
                docs[doc_id] = ranked_doc.document
        
        # Ordena por score RRF
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        return [
            RankedDocument(
                document=docs[doc_id],
                score=scores[doc_id],
                rank=i + 1,
                method="rrf",
            )
            for i, doc_id in enumerate(sorted_ids[:top_k])
        ]
    
    async def rerank(
        self,
        query: str,
        documents: List[RankedDocument],
        top_k: int = 5,
    ) -> List[RankedDocument]:
        """Re-ranking (placeholder - requer cross-encoder)."""
        # TODO: Implementar com cross-encoder
        # Por enquanto, retorna os documentos ordenados pelo score existente
        sorted_docs = sorted(documents, key=lambda x: x.score, reverse=True)
        
        return [
            RankedDocument(
                document=doc.document,
                score=doc.score,
                rank=i + 1,
                method="rerank",
            )
            for i, doc in enumerate(sorted_docs[:top_k])
        ]
