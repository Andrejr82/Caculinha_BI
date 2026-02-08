"""
Analytics Endpoints
Data analysis, metrics, export and custom queries
"""

from typing import Annotated, List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import json
import logging
import duckdb
import pyarrow as pa

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.app.api.dependencies import get_current_active_user
from backend.app.infrastructure.database.models import User
from backend.app.core.monitoring.metrics_dashboard import MetricsDashboard
from backend.app.config.settings import settings 
from backend.app.core.data_scope_service import data_scope_service
from backend.app.core.duckdb_config import get_safe_connection

logger = logging.getLogger(__name__)

# Initialize MetricsDashboard globally
metrics_dashboard: Optional[MetricsDashboard] = None

def _initialize_metrics_dashboard():
    global metrics_dashboard
    if metrics_dashboard is None:
        metrics_dashboard = MetricsDashboard(
            query_history=None, 
            response_cache=None 
        )
        logger.info("MetricsDashboard initialized.")

_initialize_metrics_dashboard()

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class MetricsSummary(BaseModel):
    total_queries: int
    total_errors: int
    success_rate_feedback: float
    cache_hit_rate: float
    average_response_time_ms: str


class ErrorTrendItem(BaseModel):
    date: str
    error_count: int


class TopQueryItem(BaseModel):
    query: str
    count: int


@router.get("/kpis", response_model=MetricsSummary)
async def get_kpis(
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: int = Query(7, description="Number of days to look back for metrics"),
) -> MetricsSummary:
    if metrics_dashboard is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MetricsDashboard not initialized."
        )
    try:
        kpis = metrics_dashboard.get_metrics(days=days)
        return MetricsSummary(**kpis)
    except Exception as e:
        logger.error(f"Error fetching KPIs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching KPIs: {str(e)}"
        )


@router.get("/error-trend", response_model=List[ErrorTrendItem])
async def get_error_trend(
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: int = Query(30, description="Number of days to look back for error trend"),
) -> List[ErrorTrendItem]:
    if metrics_dashboard is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MetricsDashboard not initialized."
        )
    try:
        trend = metrics_dashboard.get_error_trend(days=days)
        return [ErrorTrendItem(**item) for item in trend]
    except Exception as e:
        logger.error(f"Error fetching error trend: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching error trend: {str(e)}"
        )


@router.get("/top-queries", response_model=List[TopQueryItem])
async def get_top_queries(
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: int = Query(7, description="Number of days to look back for top queries"),
    limit: int = Query(10, description="Maximum number of top queries to return"),
) -> List[TopQueryItem]:
    if metrics_dashboard is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MetricsDashboard not initialized."
        )
    try:
        top_queries = metrics_dashboard.get_top_queries(days=days, limit=limit)
        return [TopQueryItem(**item) for item in top_queries]
    except Exception as e:
        logger.error(f"Error fetching top queries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top queries: {str(e)}"
        )


@router.get("/filter-options")
async def get_filter_options(
    current_user: Annotated[User, Depends(get_current_active_user)],
    segmento: Optional[str] = Query(None, description="Segmento para filtrar as categorias retornadas"),
    categoria: Optional[str] = Query(None, description="Categoria para filtrar os grupos retornados")
) -> Dict[str, List[str]]:
    try:
        # Create safe connection for streaming
        conn = get_safe_connection()
        
        # Get lazy relation directly (True Streaming)
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        # Check if empty (efficiently)
        try:
            # Quick check if relation has data without full scan if possible, 
            # but for filter options we need scan anyway.
            # DuckDB relation doesn't have is_empty property easily without query.
            # We can skip check and let queries return empty.
            cols = rel.columns
        except Exception:
            # Likely execution error or empty
            return {"categorias": [], "segmentos": [], "grupos": []}

        # Helper to get distinct list
        def get_distinct(rel_obj, col):
            if col not in cols: return []
            res = rel_obj.select(col).distinct().order(col).fetchall()
            return [str(r[0]).strip() for r in res if r[0] and str(r[0]).strip() not in ['null', 'None']]

        # Apply Filters
        if segmento and "NOMESEGMENTO" in cols:
            rel = rel.filter(f"LOWER(NOMESEGMENTO) = '{segmento.lower()}'")
        
        if categoria and "NOMECATEGORIA" in cols:
            rel = rel.filter(f"LOWER(NOMECATEGORIA) = '{categoria.lower()}'")

        categorias = get_distinct(rel, "NOMECATEGORIA")
        grupos = get_distinct(rel, "NOMEGRUPO")

        # Segments always from base (unfiltered by other selections to allow changing selection)
        # Segments always from base (unfiltered by other selections to allow changing selection)
        # Re-fetch base for segments using SAME connection
        base_rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        segmentos = get_distinct(base_rel, "NOMESEGMENTO")

        return {
            "categorias": categorias,
            "segmentos": segmentos,
            "grupos": grupos
        }

    except Exception as e:
        logger.error(f"Error getting filter options: {e}", exc_info=True)
        # Cannot access arrow_table.num_rows here anymore
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting filter options: {str(e)}"
        )


@router.get("/sales-analysis")
async def get_sales_analysis(
    current_user: Annotated[User, Depends(get_current_active_user)],
    categoria: Optional[str] = Query(None),
    segmento: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None)
) -> Dict[str, Any]:
    try:
        # Create safe connection for streaming
        conn = get_safe_connection()
        
        # Get lazy relation (True Streaming)
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)

        try:
             cols = rel.columns
        except Exception:
             return {
                "vendas_por_categoria": [],
                "giro_estoque": [],
                "distribuicao_abc": {"A": 0, "B": 0, "C": 0, "detalhes": []}
            }

        logger.info(f"Processing sales analysis (Streaming Mode)")

        chart_title = "Vendas por Categoria" # Default fallback

        # Usar nomes UPPERCASE do Parquet (padrão garantido)
        categoria_col = "NOMECATEGORIA"
        segmento_col = "NOMESEGMENTO"
        grupo_col = "NOMEGRUPO"
        produto_col = "PRODUTO"
        nome_col = "NOME"
        venda_col = "VENDA_30DD"
        estoque_col = "ESTOQUE_UNE"

        # Apply Filters
        if categoria and categoria_col:
            rel = rel.filter(f"LOWER({categoria_col}) = '{categoria.lower()}'")
        if segmento and segmento_col:
            rel = rel.filter(f"LOWER({segmento_col}) = '{segmento.lower()}'")
        if grupo and grupo_col:
            rel = rel.filter(f"LOWER({grupo_col}) = '{grupo.lower()}'")

        # 1. Sales by Category (Dynamic Drill-down)
        vendas_categoria = []
        chart_title = "Vendas por Categoria (Top 10)"
        breakdown_col = categoria_col

        # Dynamic Drill-down Logic
        if grupo and grupo_col and produto_col and nome_col:
             # Drill down to Product Level
             breakdown_col = nome_col
             chart_title = "Top Produtos no Grupo (Top 10)"
        elif categoria and categoria_col and grupo_col:
             # Drill down to Group Level
             breakdown_col = grupo_col
             chart_title = "Vendas por Grupo (Top 10)"
        
        if breakdown_col and venda_col:
            sql = f"""
                SELECT {breakdown_col}, SUM(TRY_CAST({venda_col} AS DOUBLE)) as v
                FROM cat_sales
                GROUP BY {breakdown_col}
                ORDER BY v DESC
                LIMIT 10
            """
            rows = rel.query("cat_sales", sql).fetchall()
            for r in rows:
                vendas_categoria.append({
                    "categoria": str(r[0])[:30], # Label ("categoria") mantido para compatibilidade frontend
                    "vendas": int(r[1] or 0)
                })

        # 2. Stock Turn (Giro)
        giro_estoque = []
        if venda_col and estoque_col and produto_col and nome_col:
            sql = f"""
                SELECT {produto_col}, {nome_col},
                       SUM(TRY_CAST({venda_col} AS DOUBLE)) as vendas,
                       AVG(TRY_CAST({estoque_col} AS DOUBLE)) as est_medio
                FROM giro
                WHERE TRY_CAST({venda_col} AS DOUBLE) > 0 AND TRY_CAST({estoque_col} AS DOUBLE) > 0
                GROUP BY {produto_col}, {nome_col}
                ORDER BY (vendas / est_medio) DESC
                LIMIT 15
            """
            rows = rel.query("giro", sql).fetchall()
            for r in rows:
                vendas = float(r[2] or 0)
                est_medio = float(r[3] or 1) # avoid div by zero
                giro = vendas / est_medio if est_medio > 0 else 0
                giro_estoque.append({
                    "produto": str(r[0]),
                    "nome": str(r[1])[:40],
                    "giro": round(giro, 2)
                })

        # 3. ABC Distribution
        distribuicao_abc = {"A": 0, "B": 0, "C": 0, "detalhes": [], "receita_por_classe": {}}
        val_col = "MES_01" if "MES_01" in cols else venda_col

        if val_col and produto_col and nome_col:
            # Check empty
            count = rel.filter(f"TRY_CAST({val_col} AS DOUBLE) > 0").count("*").fetchone()[0]
            if count > 0:
                # Calculate ABC in SQL
                # Window functions are great here
                abc_sql = f"""
                    WITH product_sales AS (
                        SELECT
                            {produto_col} as PRODUTO,
                            {nome_col} as NOME,
                            TRY_CAST({val_col} AS DOUBLE) as receita
                        FROM rel
                        WHERE TRY_CAST({val_col} AS DOUBLE) > 0
                    ),
                    total AS (
                        SELECT SUM(receita) as total_rev FROM product_sales
                    ),
                    cumul AS (
                        SELECT 
                            PRODUTO, NOME, receita,
                            SUM(receita) OVER (ORDER BY receita DESC) as running_sum,
                            (SUM(receita) OVER (ORDER BY receita DESC) / (SELECT total_rev FROM total)) * 100 as perc_acumulada
                        FROM product_sales
                    )
                    SELECT 
                        PRODUTO, NOME, receita, perc_acumulada,
                        CASE 
                            WHEN perc_acumulada <= 80 THEN 'A'
                            WHEN perc_acumulada <= 95 THEN 'B'
                            ELSE 'C'
                        END as classe
                    FROM cumul
                    ORDER BY receita DESC
                """
                
                # Execute full query
                # Note: DuckDB CTEs in rel.query work, but 'FROM rel' inside CTE
                # must refer to the alias registered by rel.query("abc", ...).
                # Actually, inside CTE 'FROM rel' is tricky. 
                # Better to use implicit context or alias.
                # If we name alias 'rel_data', then FROM rel_data.
                # Here we used alias 'abc'. So internal FROM should be FROM abc? No.
                # 'abc' is result. 
                # Correct pattern: 
                # rel.query("my_view", "SELECT ... FROM my_view ...") 
                # so the base table is accessible as 'my_view'.
                
                abc_sql = abc_sql.replace("FROM rel", "FROM abc") 
                abc_rel = rel.query("abc", abc_sql)
                
                # Summary
                summary_sql = "SELECT classe, COUNT(*), SUM(receita) FROM abc_rel GROUP BY classe"
                summary_rows = abc_rel.query("summ", summary_sql).fetchall()
                
                for r in summary_rows:
                    cls, qtd, soma = r
                    distribuicao_abc[cls] = qtd
                    distribuicao_abc["receita_por_classe"][cls] = soma
                
                # Details (Top 20)
                details_rows = abc_rel.limit(20).fetchall()
                # Cols: PRODUTO, NOME, receita, perc, classe
                for r in details_rows:
                    distribuicao_abc["detalhes"].append({
                        "PRODUTO": str(r[0]),
                        "NOME": str(r[1]),
                        "receita": float(r[2]),
                        "perc_acumulada": float(r[3]),
                        "classe": str(r[4])
                    })

        return {
            "vendas_por_categoria": vendas_categoria,
            "chart_title": chart_title,
            "giro_estoque": giro_estoque,
            "distribuicao_abc": distribuicao_abc
        }

    except Exception as e:
        logger.error(f"Error in sales analysis: {e}", exc_info=True)
        logger.error(f"Filters applied - categoria: {categoria}, segmento: {segmento}, grupo: {grupo}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing sales: {str(e)}"
        )


class ABCDetailItem(BaseModel):
    PRODUTO: str
    NOME: str
    UNE: str
    UNE_NOME: Optional[str]
    receita: float
    perc_acumulada: float
    classe: str


@router.get("/abc-details", response_model=List[ABCDetailItem])
async def get_abc_details(
    current_user: Annotated[User, Depends(get_current_active_user)],
    classe: str = Query(..., description="Classe ABC (A, B ou C)"),
    categoria: Optional[str] = Query(None),
    segmento: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None)
) -> List[ABCDetailItem]:
    try:
        if classe not in ['A', 'B', 'C']:
            raise HTTPException(status_code=400, detail="Classe must be A, B, or C")

        # Create safe connection for streaming
        conn = get_safe_connection()
        
        # Get lazy relation (True Streaming)
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
             cols = rel.columns
        except Exception:
             return []

        logger.info(f"Processing ABC details for classe {classe} (Streaming Mode)")

        # Usar nomes UPPERCASE do Parquet (padrão garantido)
        categoria_col = "NOMECATEGORIA"
        segmento_col = "NOMESEGMENTO"
        grupo_col = "NOMEGRUPO"
        produto_col = "PRODUTO"
        nome_col = "NOME"
        une_col = "UNE"
        une_nome_col = "UNE_NOME"
        val_col = "MES_01" if "MES_01" in cols else "VENDA_30DD"

        if not val_col: return []

        # Filters
        if categoria and categoria_col:
            rel = rel.filter(f"LOWER({categoria_col}) = '{categoria.lower()}'")
        if segmento and segmento_col:
            rel = rel.filter(f"LOWER({segmento_col}) = '{segmento.lower()}'")
        if grupo and grupo_col:
            rel = rel.filter(f"LOWER({grupo_col}) = '{grupo.lower()}'")

        # ABC Logic (Reused)
        une_sel = f"{une_col} as UNE," if une_col else "'N/A' as UNE,"
        une_nome_sel = f"{une_nome_col} as UNE_NOME," if une_nome_col else "NULL as UNE_NOME,"

        abc_sql = f"""
            WITH product_sales AS (
                SELECT
                    {produto_col} as PRODUTO,
                    {nome_col} as NOME,
                    {une_sel}
                    {une_nome_sel}
                    TRY_CAST({val_col} AS DOUBLE) as receita
                FROM abc_det
                WHERE TRY_CAST({val_col} AS DOUBLE) > 0
            ),
            total AS (
                SELECT SUM(receita) as total_rev FROM product_sales
            ),
            cumul AS (
                SELECT 
                    *,
                    (SUM(receita) OVER (ORDER BY receita DESC) / (SELECT total_rev FROM total)) * 100 as perc_acumulada
                FROM product_sales
            ),
            classified AS (
                SELECT 
                    *,
                    CASE 
                        WHEN perc_acumulada <= 80 THEN 'A'
                        WHEN perc_acumulada <= 95 THEN 'B'
                        ELSE 'C'
                    END as classe
                FROM cumul
            )
            SELECT * FROM classified WHERE classe = '{classe}'
        """
        
        rows = rel.query("abc_det", abc_sql).fetchall()
        
        results = []
        # Cols: PRODUTO, NOME, UNE, UNE_NOME, receita, perc, classe (implied by where)
        # Note: Window functions might shift col order slightly in select *, explicit is better but verify
        # DuckDB select * from CTE preserves order usually.
        # Let's map by index assuming order: PRODUTO, NOME, UNE, UNE_NOME, receita, perc_acumulada, classe
        
        for r in rows:
            results.append(ABCDetailItem(
                PRODUTO=str(r[0]),
                NOME=str(r[1]),
                UNE=str(r[2]),
                UNE_NOME=str(r[3]) if r[3] else None,
                receita=float(r[4]),
                perc_acumulada=float(r[5]),
                classe=str(r[6])
            ))

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ABC details: {e}", exc_info=True)
        logger.error(f"Filters - classe: {classe}, categoria: {categoria}, segmento: {segmento}, grupo: {grupo}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting ABC details: {str(e)}"
        )

