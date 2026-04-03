"""
Ferramenta de busca híbrida de produtos usando embeddings locais + keyword ranking.

Objetivo:
- Resolver nomes vagos, sinônimos, typos e descrições incompletas.
- Usar apenas runtime oficial local para retrieval, sem dependência de Gemini.
- Retornar detalhes operacionais reais do parquet da Caçula.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import duckdb

try:
    from langchain_core.tools import tool
except (ImportError, OSError):  # pragma: no cover - fallback de ambiente
    def tool(func):
        return func

from backend.app.config.settings import settings
from backend.app.core.retrieval.embedding_backend import get_embedding_backend

logger = logging.getLogger(__name__)

_PRODUCT_INDEX_CACHE: Dict[str, Any] | None = None


def _resolve_parquet_path() -> Path:
    parquet_path = Path(settings.PARQUET_DATA_PATH)
    if parquet_path.exists():
        return parquet_path
    raise FileNotFoundError(f"Parquet principal não encontrado: {parquet_path}")


def _escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _tokenize(value: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", (value or "").lower()) if len(token) > 1]


def _keyword_rank(query: str, rows: List[Dict[str, Any]], limit: int) -> List[str]:
    query_lower = (query or "").lower().strip()
    tokens = _tokenize(query_lower)
    scored: List[Tuple[float, str]] = []

    for row in rows:
        code = str(row["codigo"])
        searchable = str(row["searchable"]).lower()
        name = str(row["nome"]).lower()

        score = 0.0
        if query_lower and query_lower in searchable:
            score += 4.0
        if query_lower and query_lower in name:
            score += 6.0
        if code == query_lower:
            score += 10.0

        for token in tokens:
            if token in name:
                score += 2.0
            elif token in searchable:
                score += 1.0

        if score > 0:
            scored.append((score, code))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [code for _, code in scored[:limit]]


def _reciprocal_rank_fusion(
    semantic_results: List[str],
    keyword_results: List[str],
    limit: int = 10,
    k: int = 60,
) -> List[str]:
    scores: Dict[str, float] = {}

    for rank, code in enumerate(semantic_results, start=1):
        scores[code] = scores.get(code, 0.0) + (1.0 / (k + rank))

    for rank, code in enumerate(keyword_results, start=1):
        scores[code] = scores.get(code, 0.0) + (1.0 / (k + rank))

    merged = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [code for code, _ in merged[:limit]]


def _build_product_index() -> Dict[str, Any]:
    parquet_path = _resolve_parquet_path()
    escaped_path = _escape_path(parquet_path)

    with duckdb.connect(":memory:") as con:
        rows = con.execute(
            f"""
            SELECT DISTINCT
                CAST(PRODUTO AS VARCHAR) AS codigo,
                COALESCE(NOME, '') AS nome,
                COALESCE(NOMESEGMENTO, '') AS segmento,
                COALESCE(NOMECATEGORIA, '') AS categoria
            FROM read_parquet('{escaped_path}')
            """
        ).fetchall()

    products: List[Dict[str, Any]] = []
    texts: List[str] = []
    for codigo, nome, segmento, categoria in rows:
        searchable = " | ".join(
            part for part in [str(codigo), str(nome), str(segmento), str(categoria)] if part
        )
        products.append(
            {
                "codigo": str(codigo),
                "nome": str(nome),
                "segmento": str(segmento),
                "categoria": str(categoria),
                "searchable": searchable,
            }
        )
        texts.append(searchable)

    embedding_backend = get_embedding_backend()
    embeddings = embedding_backend.embed_batch(texts)
    logger.info("Índice semântico de produtos carregado: %s itens", len(products))
    return {
        "parquet_path": parquet_path,
        "mtime": parquet_path.stat().st_mtime,
        "rows": products,
        "embeddings": embeddings,
    }


def _ensure_product_index() -> Dict[str, Any]:
    global _PRODUCT_INDEX_CACHE
    parquet_path = _resolve_parquet_path()
    current_mtime = parquet_path.stat().st_mtime

    if (
        _PRODUCT_INDEX_CACHE is None
        or _PRODUCT_INDEX_CACHE.get("parquet_path") != parquet_path
        or _PRODUCT_INDEX_CACHE.get("mtime") != current_mtime
    ):
        _PRODUCT_INDEX_CACHE = _build_product_index()

    return _PRODUCT_INDEX_CACHE


def _semantic_rank(query: str, rows: List[Dict[str, Any]], embeddings: List[List[float]], limit: int) -> List[str]:
    backend = get_embedding_backend()
    query_embedding = backend.embed_text(query)
    scored: List[Tuple[float, str]] = []

    for row, embedding in zip(rows, embeddings):
        if not embedding:
            continue
        similarity = backend.cosine_similarity(query_embedding, embedding)
        if similarity > 0:
            scored.append((similarity, str(row["codigo"])))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [code for _, code in scored[:limit]]


def _fetch_details(parquet_path: Path, codes: List[str], limit: int) -> List[Dict[str, Any]]:
    if not codes:
        return []

    escaped_path = _escape_path(parquet_path)
    safe_codes = ", ".join("'" + str(code).replace("'", "''") + "'" for code in codes)
    with duckdb.connect(":memory:") as con:
        df = con.execute(
            f"""
            SELECT DISTINCT
                CAST(PRODUTO AS VARCHAR) AS PRODUTO,
                NOME,
                NOMESEGMENTO,
                NOMECATEGORIA,
                LIQUIDO_38 AS PRECO_VENDA,
                ESTOQUE_UNE,
                VENDA_30DD,
                UNE
            FROM read_parquet('{escaped_path}')
            WHERE CAST(PRODUTO AS VARCHAR) IN ({safe_codes})
            """
        ).fetchdf()

    if df.empty:
        return []

    df["PRODUTO"] = df["PRODUTO"].astype(str)
    df["__rank"] = df["PRODUTO"].map({code: idx for idx, code in enumerate(codes)})
    df = df.sort_values(["__rank", "VENDA_30DD"], ascending=[True, False]).drop(columns=["__rank"])
    return df.head(limit).to_dict(orient="records")


@tool
def buscar_produtos_inteligente(
    descricao: str,
    limite: int = 50,
    usar_hybrid: bool = True,
) -> Dict[str, Any]:
    """
    Busca produtos usando retrieval híbrido local com tolerância a typos e sinônimos.

    USE QUANDO: o usuário descrever um produto de forma vaga, incompleta ou com sinônimos.
    NÃO use para código exato; para isso prefira consultar_dados_flexivel.
    """
    logger.info("Busca inteligente de produtos: '%s' (limite=%s, hybrid=%s)", descricao, limite, usar_hybrid)

    try:
        index = _ensure_product_index()
        rows = index["rows"]
        embeddings = index["embeddings"]
        parquet_path = index["parquet_path"]

        semantic_codes = _semantic_rank(descricao, rows, embeddings, max(limite * 2, 10))
        keyword_codes = _keyword_rank(descricao, rows, max(limite * 2, 10))

        if usar_hybrid:
            merged_codes = _reciprocal_rank_fusion(
                semantic_results=semantic_codes,
                keyword_results=keyword_codes,
                limit=limite,
            )
            search_type = "hybrid_local_rrf"
        else:
            merged_codes = semantic_codes[:limite] or keyword_codes[:limite]
            search_type = "semantic_local_only" if semantic_codes else "keyword_only"

        produtos = _fetch_details(parquet_path, merged_codes, limite)

        return {
            "status": "success",
            "search_type": search_type,
            "total_encontrados": len(produtos),
            "produtos": produtos,
            "stats": {
                "semantic_matches": len(semantic_codes),
                "keyword_matches": len(keyword_codes),
                "merged_results": len(merged_codes),
            },
            "message": f"Encontrados {len(produtos)} produtos via busca inteligente local",
        }

    except Exception as exc:
        logger.error("Erro na busca inteligente de produtos: %s", exc, exc_info=True)
        return {
            "status": "error",
            "message": f"Erro ao buscar produtos: {exc}",
            "fallback": "Use consultar_dados_flexivel para busca tradicional por código ou filtro exato",
        }


@tool
def reinicializar_vector_store() -> Dict[str, Any]:
    """
    Reinicializa o índice local de busca de produtos.
    """
    global _PRODUCT_INDEX_CACHE
    _PRODUCT_INDEX_CACHE = None

    try:
        index = _ensure_product_index()
        return {
            "status": "success",
            "message": "Índice local de produtos reinicializado com sucesso",
            "items_indexados": len(index.get("rows", [])),
        }
    except Exception as exc:
        logger.error("Erro ao reinicializar índice local de produtos: %s", exc, exc_info=True)
        return {
            "status": "error",
            "message": f"Erro: {exc}",
        }
