"""
Semantic Cache - Cache inteligente baseado em similaridade semântica
Permite respostas instantâneas para perguntas similares
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Cache semântico para respostas do ChatBI.
    
    Características:
    - Hash baseado em normalização da query
    - TTL configurável
    - Persistência em disco
    - Estatísticas de hit/miss
    """
    
    def __init__(
        self, 
        cache_dir: str = "data/cache/semantic",
        ttl_minutes: int = 360,  # 6 horas
        max_entries: int = 1000
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_minutes * 60
        self.max_entries = max_entries
        
        # Estatísticas
        self.hits = 0
        self.misses = 0
        
        # Index em memória para busca rápida
        self._index: Dict[str, Dict[str, Any]] = {}
        self._load_index()
        
        logger.info(f"SemanticCache inicializado: {cache_dir}, TTL={ttl_minutes}min")
    
    def _normalize_query(self, query: str) -> str:
        """
        Normaliza query para melhor matching.
        IMPORTANTE: Preserva números (UNE, produto, etc) para evitar cache incorreto.
        """
        import re

        # Converter para minúsculas
        normalized = query.lower().strip()

        # Remover pontuação desnecessária
        for char in "?!.,;:":
            normalized = normalized.replace(char, "")

        # Normalizar espaços múltiplos
        normalized = " ".join(normalized.split())

        # [OK] FIX 2026-01-14: Extrair e PRESERVAR números importantes (UNE, produto, etc)
        # Isso evita que "vendas UNE 1685" seja igual a "vendas UNE 1700"
        numbers = re.findall(r'\b\d{3,}\b', normalized)  # Números com 3+ dígitos
        if numbers:
            # Adiciona hash dos números ao final para diferenciar queries
            numbers_hash = "_".join(sorted(numbers))
            normalized = f"{normalized}__NUMS:{numbers_hash}"

        return normalized
    
    def _generate_key(self, query: str, user_id: Optional[str] = None) -> str:
        """
        Gera chave hash para a query normalizada.

        [OK] FIX 2026-01-14: Inclui user_id no hash para isolamento de cache por usuário.
        Isso evita que analyst veja cache de admin com dados de segmentos diferentes.
        """
        normalized = self._normalize_query(query)
        # Se user_id fornecido, inclui no hash para isolamento
        if user_id:
            key_source = f"{user_id}::{normalized}"
        else:
            key_source = normalized
        return hashlib.md5(key_source.encode('utf-8')).hexdigest()

    def _extract_critical_numbers(self, text: str) -> set:
        """
        Extrai números críticos (UNE, produto, etc.) de uma query.
        Números com 3+ dígitos são considerados identificadores de filtro.
        """
        import re
        return set(re.findall(r'\b\d{3,}\b', text))

    def _find_similar_entry(self, normalized_query: str, user_id: Optional[str] = None) -> Tuple[Optional[str], float]:
        """
        Busca entrada similar no índice usando similaridade de strings.

        [OK] FIX 2026-01-14: REJEITA fuzzy matches se:
        - Números críticos (UNE, produto) forem diferentes
        - user_id fornecido e não corresponder ao cache

        Isso impede que "vendas UNE 1685" retorne cache de "vendas UNE 1700".

        Performance optimization: Limitado às últimas 100 queries para não pesar CPU.
        Returns: (key, similarity_score)
        """
        from difflib import SequenceMatcher

        best_score = 0.0
        best_key = None

        # [OK] FIX: Extrair números da query ANTES de comparar
        query_numbers = self._extract_critical_numbers(normalized_query)

        # OTIMIZAÇÃO: Verificar apenas entradas recentes para performance
        recent_items = sorted(
            self._index.items(),
            key=lambda x: x[1].get("timestamp", 0),
            reverse=True
        )[:100]

        for key, data in recent_items:
            # [OK] FIX: Filtrar por user_id se fornecido
            if user_id:
                cached_user = data.get("user_id")
                if cached_user and cached_user != user_id:
                    continue  # REJEITA - usuário diferente

            cached_norm = data.get("normalized", "")
            if not cached_norm:
                continue

            # [OK] FIX CRÍTICO: Se a query tem números, o cache DEVE ter os MESMOS números
            cached_numbers = self._extract_critical_numbers(cached_norm)

            if query_numbers or cached_numbers:
                if query_numbers != cached_numbers:
                    continue  # REJEITA - números diferentes = dados diferentes

            # Quick fail por tamanho
            if abs(len(normalized_query) - len(cached_norm)) > len(normalized_query) * 0.3:
                continue

            # Calcular similaridade
            score = SequenceMatcher(None, normalized_query, cached_norm).ratio()

            if score > best_score:
                best_score = score
                best_key = key

                if best_score > 0.95:
                    return best_key, best_score

        return best_key, best_score
    
    def _load_index(self):
        """Carrega índice do disco."""
        index_file = self.cache_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
                logger.info(f"Cache index carregado: {len(self._index)} entradas")
            except Exception as e:
                logger.error(f"Erro ao carregar cache index: {e}")
                self._index = {}
    
    def _save_index(self):
        """Salva índice no disco."""
        index_file = self.cache_dir / "index.json"
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar cache index: {e}")
    
    def get(self, query: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Busca resposta em cache.

        Args:
            query: Pergunta do usuário
            user_id: ID do usuário para isolamento de cache ([OK] FIX 2026-01-14)

        Returns:
            Resposta cacheada ou None se não encontrada/expirada
        """
        key = self._generate_key(query, user_id)
        normalized = self._normalize_query(query)

        logger.debug(f"Cache GET - Query: '{query}' | User: {user_id} | Key: {key}")

        if key not in self._index:
            # Fuzzy matching com verificação de números críticos
            similar_key, similarity = self._find_similar_entry(normalized, user_id)
            if similar_key and similarity >= 0.95:
                logger.info(f"Cache FUZZY HIT: '{query}' ~= '{self._index[similar_key]['query']}' (sim={similarity:.2f})")
                key = similar_key
                self._index[key]['timestamp'] = time.time()
                self._save_index()
            else:
                self.misses += 1
                logger.debug(f"Cache MISS - Key not in index (user={user_id})")
                return None

        entry = self._index[key]

        # [OK] FIX: Verificar se o user_id do cache corresponde (se fornecido)
        cached_user = entry.get("user_id")
        if user_id and cached_user and cached_user != user_id:
            self.misses += 1
            logger.debug(f"Cache MISS - User mismatch: {cached_user} != {user_id}")
            return None

        # Verificar TTL
        if time.time() - entry.get("timestamp", 0) > self.ttl_seconds:
            self._remove_entry(key)
            self.misses += 1
            logger.debug(f"Cache expirado para: {query[:50]}...")
            return None

        # Cache hit!
        self.hits += 1
        logger.info(f"Cache HIT para: {query[:50]}... (user={user_id}, hits={self.hits})")

        # Carregar resposta do arquivo
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao ler cache file: {e}")
                return None

        return None
    
    def set(self, query: str, response: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """
        Armazena resposta em cache.

        Args:
            query: Pergunta do usuário
            response: Resposta a cachear
            user_id: ID do usuário para isolamento de cache ([OK] FIX 2026-01-14)

        Returns:
            True se armazenado com sucesso
        """
        key = self._generate_key(query, user_id)

        # Verificar limite de entradas
        if len(self._index) >= self.max_entries:
            self._cleanup_oldest()

        # Atualizar índice com user_id para isolamento
        self._index[key] = {
            "query": query,
            "normalized": self._normalize_query(query),
            "timestamp": time.time(),
            "user_id": user_id,  # [OK] FIX: Armazena user_id para filtragem
        }

        # Salvar resposta em arquivo
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)

            self._save_index()
            logger.debug(f"Cache SET para: {query[:50]}... (user={user_id})")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
            return False
    
    def _remove_entry(self, key: str):
        """Remove entrada do cache."""
        if key in self._index:
            del self._index[key]
            
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            cache_file.unlink()
        
        self._save_index()
    
    def _cleanup_oldest(self, remove_count: int = 100):
        """Remove entradas mais antigas."""
        if not self._index:
            return
        
        # Ordenar por timestamp
        sorted_entries = sorted(
            self._index.items(),
            key=lambda x: x[1].get("timestamp", 0)
        )
        
        # Remover as mais antigas
        for key, _ in sorted_entries[:remove_count]:
            self._remove_entry(key)
        
        logger.info(f"Cache cleanup: removidas {remove_count} entradas antigas")
    
    def clear(self):
        """Limpa todo o cache."""
        for key in list(self._index.keys()):
            self._remove_entry(key)
        self._index = {}
        self._save_index()
        logger.info("Cache limpo completamente")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "entries": len(self._index),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_dir": str(self.cache_dir),
        }


# Instância global do cache
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    """Retorna instância singleton do cache."""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache


# Funções de conveniência
def cache_get(query: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Busca resposta em cache.

    [OK] FIX 2026-01-14: user_id agora é usado para isolamento de cache por usuário.
    """
    return get_semantic_cache().get(query, user_id)


def cache_set(query: str, response: Dict[str, Any], user_id: Optional[str] = None) -> bool:
    """
    Armazena resposta em cache.

    [OK] FIX 2026-01-14: user_id agora é usado para isolamento de cache por usuário.
    """
    return get_semantic_cache().set(query, response, user_id)


def cache_stats() -> Dict[str, Any]:
    """Retorna estatísticas do cache."""
    return get_semantic_cache().get_stats()
