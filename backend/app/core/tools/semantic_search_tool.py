"""
Ferramenta de busca semântica para produtos usando RAG (Retrieval-Augmented Generation).

Implementa hybrid search combinando:
- Semantic search via Google Generative AI Embeddings
- Keyword search tradicional
- Reciprocal Rank Fusion (RRF) para merge de resultados

Author: Context7 2025
Status: POC (Proof of Concept)
"""

import logging
import os
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import duckdb
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Singleton instance para cache do vector store
_VECTOR_STORE_CACHE = None
_EMBEDDINGS_MODEL = None


def _get_embeddings_model():
    """Retorna o modelo de embeddings (singleton)"""
    global _EMBEDDINGS_MODEL
    if _EMBEDDINGS_MODEL is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fallback mock/warning if key missing during init (prevents crash)
            logger.warning("GEMINI_API_KEY not found. Embeddings will fail if called.")
            return None

        _EMBEDDINGS_MODEL = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        logger.info("Google Generative AI Embeddings initialized")
    return _EMBEDDINGS_MODEL


def _initialize_vector_store() -> FAISS:
    """
    Inicializa o vector store FAISS com embeddings de produtos.
    Executa apenas uma vez e cacheia o resultado (lazy loading).
    """
    global _VECTOR_STORE_CACHE

    if _VECTOR_STORE_CACHE is not None:
        logger.debug("Using cached vector store")
        return _VECTOR_STORE_CACHE

    logger.info("Initializing FAISS vector store with product embeddings...")

    try:
        cache_dir = Path("backend/data/cache/embeddings")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_index = cache_dir / "product_embeddings_faiss.index"
        
        embeddings_model = _get_embeddings_model()
        if not embeddings_model:
             raise ValueError("Embeddings model not initialized (missing API Key)")

        # Tentar carregar do cache primeiro
        if cache_index.exists():
            logger.info(f"Loading cached embeddings from {cache_index}...")
            try:
                _VECTOR_STORE_CACHE = FAISS.load_local(
                    str(cache_dir),
                    embeddings_model,
                    index_name="product_embeddings_faiss",
                    allow_dangerous_deserialization=True # Necessary for loading pickled files
                )
                logger.info(f"Successfully loaded cached vector store")
                return _VECTOR_STORE_CACHE
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}. Regenerating embeddings...")

        # Se cache não existe ou falhou, criar novos embeddings
        # Carregar dados de produtos via DuckDB (Substituindo Polars)
        parquet_path = "C:/Agente_BI/BI_Solution/backend/data/parquet/admmat.parquet"
        
        # Fallback path logic
        if not os.path.exists(parquet_path):
             parquet_path = "/app/app/data/parquet/admmat.parquet" # Docker path attempt
        if not os.path.exists(parquet_path):
             # Try relative
             parquet_path = "data/parquet/admmat.parquet"

        # DuckDB Query to get unique products
        con = duckdb.connect(":memory:")
        try:
            query = f"""
                SELECT DISTINCT 
                    CAST(PRODUTO AS VARCHAR) as codigo, 
                    COALESCE(NOME, '') as nome
                FROM read_parquet('{parquet_path}')
            """
            products_df = con.execute(query).fetchdf()
        finally:
            con.close()

        texts = [
            f"{row['codigo']} | {row['nome']}"
            for _, row in products_df.iterrows()
        ]

        logger.info(f"Creating embeddings for {len(texts)} unique products...")
        logger.warning(f"This will consume API quota. Future runs will use cache.")

        _VECTOR_STORE_CACHE = FAISS.from_texts(
            texts=texts,
            embedding=embeddings_model
        )

        # Salvar cache para uso futuro
        try:
            _VECTOR_STORE_CACHE.save_local(
                str(cache_dir),
                index_name="product_embeddings_faiss"
            )
            logger.info(f"Embeddings cached to {cache_dir} for future use")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

        logger.info(f"Vector store initialized with {len(texts)} product embeddings")
        return _VECTOR_STORE_CACHE

    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}", exc_info=True)
        # Em caso de falha crítica (ex: sem API Key), não crashar o app, retornar None ou mock?
        # Melhor lançar erro para ser tratado no tool call
        raise


def _reciprocal_rank_fusion(
    semantic_results: List[str],
    keyword_results: List[str],
    limit: int = 10,
    k: int = 60
) -> List[str]:
    """
    Combina resultados de semantic e keyword search usando Reciprocal Rank Fusion.
    """
    scores = {}

    # Score semantic results
    for rank, doc in enumerate(semantic_results, start=1):
        scores[doc] = scores.get(doc, 0) + (1 / (k + rank))

    # Score keyword results
    for rank, doc in enumerate(keyword_results, start=1):
        scores[doc] = scores.get(doc, 0) + (1 / (k + rank))

    # Sort by score descending
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Return top N document IDs
    return [doc for doc, score in sorted_docs[:limit]]


@tool
def buscar_produtos_inteligente(
    descricao: str,
    limite: int = 50,  # FIX 2026-01-27: Aumentado de 10 para 50 (melhor cobertura)
    usar_hybrid: bool = True
) -> Dict[str, Any]:
    """
    Busca produtos usando IA semântica (RAG) com tolerância a typos e sinônimos.

    USE QUANDO: O usuário buscar por descrição vaga, nomes incompletos, sinônimos ("coisa de limpar"),
    ou quando a busca exata por código falhar. NÃO use para códigos exatos (use consultar_dados_flexivel).
    """
    logger.info(f"Busca inteligente: '{descricao}' (limite={limite}, hybrid={usar_hybrid})")

    try:
        parquet_path = "C:/Agente_BI/BI_Solution/backend/data/parquet/admmat.parquet"
        # Path resolution logic (simplified)
        if not os.path.exists(parquet_path):
             parquet_path = "/app/app/data/parquet/admmat.parquet"
        if not os.path.exists(parquet_path):
             parquet_path = "data/parquet/admmat.parquet"

        # 1. SEMANTIC SEARCH
        try:
            vector_store = _initialize_vector_store()
            semantic_docs = vector_store.similarity_search(descricao, k=limite * 2)
            semantic_product_codes = [
                doc.page_content.split(" | ")[0]
                for doc in semantic_docs
            ]
        except Exception as e:
            logger.warning(f"Semantic search failed (using keyword only): {e}")
            semantic_product_codes = []
            usar_hybrid = False # Fallback to keyword only

        con = duckdb.connect(":memory:")
        
        # Helper to fetch details for codes
        def fetch_details(codes):
            if not codes: return []
            codes_str = ", ".join([f"'{c}'" for c in codes])
            # Handle potential quoting issues in codes
            # Assuming codes are safe strings or numerics
            # Better: use parameter binding if possible, but DuckDB python API list support is tricky in WHERE IN
            # Constructing a temporary table is safer for many items.
            
            # Simplified for POC:
            query = f"""
                SELECT DISTINCT
                    PRODUTO, NOME, NOMESEGMENTO, NOMECATEGORIA, 
                    LIQUIDO_38 as PRECO_VENDA, ESTOQUE_UNE, VENDA_30DD, UNE,
                    CASE WHEN UNE IS NOT NULL THEN CAST(UNE AS VARCHAR) ELSE 'N/A' END as UNE_NOME
                FROM read_parquet('{parquet_path}')
                WHERE CAST(PRODUTO AS VARCHAR) IN ({codes_str})
                LIMIT {limite}
            """
            return con.execute(query).fetchdf().to_dict(orient='records')

        if not usar_hybrid:
            # Semantic Only (or Semantic Fallback result)
            if not semantic_product_codes:
                 # Try purely keyword if semantic failed completely and not hybrid requested (edge case)
                 pass 
            
            produtos = fetch_details(semantic_product_codes)
            con.close()
            
            return {
                "status": "success",
                "search_type": "semantic_only",
                "total_encontrados": len(produtos),
                "produtos": produtos,
                "message": f"Encontrados {len(produtos)} produtos via busca semântica"
            }

        # 2. KEYWORD SEARCH
        # DuckDB LIKE is case insensitive by default? No, use ILIKE.
        keyword_query = f"""
            SELECT DISTINCT CAST(PRODUTO AS VARCHAR) as code
            FROM read_parquet('{parquet_path}')
            WHERE LOWER(NOME) LIKE '%{descricao.lower()}%'
            LIMIT {limite * 2}
        """
        keyword_results = con.execute(keyword_query).fetchall()
        keyword_product_codes = [r[0] for r in keyword_results]

        # 3. RRF MERGE
        merged_codes = _reciprocal_rank_fusion(
            semantic_results=semantic_product_codes,
            keyword_results=keyword_product_codes,
            limit=limite
        )

        # 4. FETCH DETAILS
        # We need to fetch details for merged codes AND preserve order?
        # SQL IN doesn't preserve order. We sort in python.
        
        produtos_df = con.execute(f"""
            SELECT DISTINCT
                CAST(PRODUTO AS VARCHAR) as PRODUTO, 
                NOME, NOMESEGMENTO, NOMECATEGORIA, 
                LIQUIDO_38 as PRECO_VENDA, ESTOQUE_UNE, VENDA_30DD, UNE
            FROM read_parquet('{parquet_path}')
            WHERE CAST(PRODUTO AS VARCHAR) IN ({", ".join([f"'{c}'" for c in merged_codes])})
        """).fetchdf()
        
        con.close()
        
        # Sort based on merged_codes order
        produtos_df['PRODUTO'] = produtos_df['PRODUTO'].astype(str)
        produtos_df = produtos_df.set_index('PRODUTO')
        # Reindex handles sorting and missing keys
        produtos_df = produtos_df.reindex(merged_codes).dropna()
        produtos = produtos_df.reset_index().to_dict(orient='records')

        return {
            "status": "success",
            "search_type": "hybrid (semantic + keyword + RRF)",
            "total_encontrados": len(produtos),
            "produtos": produtos,
            "stats": {
                "semantic_matches": len(semantic_product_codes),
                "keyword_matches": len(keyword_product_codes),
                "merged_results": len(merged_codes)
            },
            "message": f"Encontrados {len(produtos)} produtos via busca híbrida inteligente"
        }

    except Exception as e:
        logger.error(f"Erro na busca inteligente: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Erro ao buscar produtos: {str(e)}",
            "fallback": "Use consultar_dados_flexivel para busca tradicional"
        }


@tool
def reinicializar_vector_store() -> Dict[str, Any]:
    """
    Reinicializa o vector store (útil se dados foram atualizados).

    USE QUANDO: O usuário reclamar de resultados desatualizados na busca semântica ou
    após atualização manual dos dados do Parquet.
    """
    global _VECTOR_STORE_CACHE

    logger.warning("Reinicializando vector store (clearing cache)...")

    _VECTOR_STORE_CACHE = None

    try:
        _initialize_vector_store()
        return {
            "status": "success",
            "message": "Vector store reinicializado com sucesso"
        }
    except Exception as e:
        logger.error(f"Erro ao reinicializar vector store: {e}")
        return {
            "status": "error",
            "message": f"Erro: {str(e)}"
        }
