"""
MCP Parquet Tools - Ferramentas para buscar dados em Parquet

MIGRATED TO DUCKDB (2025-12-31)
- Queries SQL diretas (mais rápido)
- Zero loading do arquivo inteiro
- Predicate pushdown automático
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any
from langchain_core.tools import tool
import logging

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter

# Caminho para o arquivo Parquet - Fonte única: Filial_Madureira
PARQUET_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "parquet")
FILIAL_MADUREIRA_PATH = os.path.join(PARQUET_DIR, "Filial_Madureira.parquet")


@tool
def get_product_data(product_code: str) -> Dict[str, Any]:
    """
    Busca dados de um produto em Filial_Madureira.parquet usando DuckDB.

    USE QUANDO: Consultas legadas específicas por Product Code.
    PREFIRA usar 'consultar_dados_flexivel' ou 'buscar_produto' para novas queries.
    """
    logging.info(f"[DUCKDB] Buscando produto: {product_code}")

    try:
        if not os.path.exists(FILIAL_MADUREIRA_PATH):
            logging.error(f"Arquivo não encontrado: {FILIAL_MADUREIRA_PATH}")
            return {"error": "Fonte de dados não encontrada."}

        adapter = get_duckdb_adapter()
        parquet_path = str(Path(FILIAL_MADUREIRA_PATH).resolve()).replace("\\", "/")

        # Verificar qual coluna existe (CODIGO ou codigo)
        schema = adapter.connection.execute(f"""
            SELECT column_name
            FROM (DESCRIBE SELECT * FROM read_parquet('{parquet_path}'))
        """).fetchall()

        columns = [col[0] for col in schema]
        code_column = None
        if "CODIGO" in columns:
            code_column = "CODIGO"
        elif "codigo" in columns:
            code_column = "codigo"
        else:
            return {"error": "Coluna de código não encontrada."}

        # Query DuckDB direta com filtro
        result = adapter.connection.execute(f"""
            SELECT *
            FROM read_parquet('{parquet_path}')
            WHERE CAST("{code_column}" AS VARCHAR) = ?
        """, [str(product_code)]).fetchall()

        if not result:
            return {"data": f"Produto não encontrado: {product_code}"}

        # Converter para dict
        column_names = [col[0] for col in schema]
        product_info = [dict(zip(column_names, row)) for row in result]

        return {"data": product_info}

    except Exception as e:
        logging.error(f"Erro ao buscar produto: {e}", exc_info=True)
        return {"error": f"Erro ao buscar dados: {e}"}


@tool
def get_product_stock(product_id: int) -> Dict[str, Any]:
    """Retorna estoque de um produto específico em Filial_Madureira usando DuckDB."""
    logging.info(f"[DUCKDB] Buscando estoque do produto: {product_id}")

    try:
        if not os.path.exists(FILIAL_MADUREIRA_PATH):
            logging.error(f"Arquivo não encontrado: {FILIAL_MADUREIRA_PATH}")
            return {"error": "Fonte de dados não encontrada."}

        adapter = get_duckdb_adapter()
        parquet_path = str(Path(FILIAL_MADUREIRA_PATH).resolve()).replace("\\", "/")

        # Query DuckDB para buscar estoque
        result = adapter.connection.execute(f"""
            SELECT PRODUTO, ESTOQUE
            FROM read_parquet('{parquet_path}')
            WHERE CAST(PRODUTO AS VARCHAR) = ?
            LIMIT 1
        """, [str(product_id)]).fetchone()

        if not result:
            return {"data": f"Nenhum produto encontrado com o ID {product_id}."}

        produto_id, estoque = result
        return {"data": {"product_id": product_id, "stock": estoque}}

    except Exception as e:
        logging.error(f"Erro ao buscar estoque do produto: {e}", exc_info=True)
        return {
            "error": f"Ocorreu um erro inesperado ao buscar o estoque do produto: {e}"
        }


@tool
def list_product_categories() -> Dict[str, Any]:
    """
    Retorna uma lista de todas as categorias de produtos disponíveis
    no arquivo Parquet 'Filial_Madureira.parquet' usando DuckDB.
    """
    logging.info(
        "[DUCKDB] Listando categorias de produtos do arquivo Parquet 'Filial_Madureira.parquet'."
    )

    try:
        if not os.path.exists(FILIAL_MADUREIRA_PATH):
            logging.error(f"Arquivo Parquet não encontrado em: {FILIAL_MADUREIRA_PATH}")
            return {
                "error": "Fonte de dados de produtos (Filial_Madureira.parquet) não encontrada."
            }

        adapter = get_duckdb_adapter()
        parquet_path = str(Path(FILIAL_MADUREIRA_PATH).resolve()).replace("\\", "/")

        # Verificar se coluna CATEGORIA existe
        schema = adapter.connection.execute(f"""
            SELECT column_name
            FROM (DESCRIBE SELECT * FROM read_parquet('{parquet_path}'))
        """).fetchall()

        columns = [col[0] for col in schema]

        if "CATEGORIA" not in columns:
            return {
                "error": "Coluna 'CATEGORIA' não encontrada no arquivo Filial_Madureira.parquet."
            }

        # Query DuckDB para obter categorias distintas
        categories = adapter.connection.execute(f"""
            SELECT DISTINCT CATEGORIA
            FROM read_parquet('{parquet_path}')
            WHERE CATEGORIA IS NOT NULL
            ORDER BY CATEGORIA
        """).fetchall()

        # Extrair valores das tuplas
        categories_list = [cat[0] for cat in categories]

        return {"data": {"categories": categories_list}}

    except Exception as e:
        logging.error(f"Erro ao listar categorias de produtos: {e}", exc_info=True)
        return {
            "error": f"Ocorreu um erro inesperado ao listar categorias de produtos: {e}"
        }


# A lista de ferramentas agora usa DuckDB internamente
sql_tools = [
    get_product_data,
    get_product_stock,
    list_product_categories,
]
