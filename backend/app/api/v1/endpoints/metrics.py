"""
Metrics Endpoints
Dashboard metrics and summary data
"""

from typing import Annotated, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import duckdb
import pyarrow as pa
import logging

from backend.app.api.dependencies import get_current_active_user
from backend.app.infrastructure.database.models import User
from backend.app.core.data_scope_service import data_scope_service
from backend.app.core.duckdb_config import get_safe_connection 

router = APIRouter(prefix="/metrics", tags=["Metrics"])
logger = logging.getLogger(__name__)

class MetricsSummary(BaseModel):
    totalSales: int
    totalUsers: int
    revenue: float
    productsCount: int
    salesGrowth: float
    usersGrowth: float

@router.get("/summary", response_model=MetricsSummary)
async def get_metrics_summary(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MetricsSummary:
    """
    Get dashboard metrics summary using DuckDB/Arrow
    """
    try:
        # Use configured connection for streaming
        conn = get_safe_connection()
        
        # Get lazy relation directly (True Streaming)
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
            # Check if valid (lazy check)
            cols = rel.columns
        except Exception:
             return MetricsSummary(totalSales=0, totalUsers=0, revenue=0.0, productsCount=0, salesGrowth=0.0, usersGrowth=0.0)

        logger.info(f"Processing metrics summary (Streaming Mode)")
        
        # Usar nomes UPPERCASE do Parquet (padrão garantido)
        c_produto = "PRODUTO"
        c_venda = "VENDA_30DD"
        c_une = "UNE"
        c_receita = "MES_01"

        # Aggregation Query
        # We construct a SQL query on the relation 'rel'
        # DuckDB Python API allows SQL on relation: rel.query("metric", "SELECT ...")
        
        # Build aggregation expression
        # COALESCE to handle nulls
        agg_sql = f"""
            SELECT 
                COUNT(DISTINCT {c_produto}) as products_count,
                SUM(COALESCE(TRY_CAST({c_venda} AS BIGINT), 0)) as total_sales,
                SUM(COALESCE(TRY_CAST({c_receita} AS DOUBLE), 0)) as revenue,
                COUNT(DISTINCT {c_une}) as total_users
            FROM metrics_sum
        """
        
        # Execute
        res = rel.query("metrics_sum", agg_sql).fetchone()
        products_count, total_sales, revenue, total_users = res

        # Calculate Growth (Sales Growth)
        sales_growth = 0.0
        if "MES_01" in cols and "MES_02" in cols:
            growth_sql = """
                SELECT 
                    SUM(COALESCE(TRY_CAST(MES_01 AS DOUBLE), 0)) as m1,
                    SUM(COALESCE(TRY_CAST(MES_02 AS DOUBLE), 0)) as m2
                FROM metrics_growth
            """
            g_res = rel.query("metrics_growth", growth_sql).fetchone()
            if g_res:
                m1, m2 = g_res
                if m2 > 0:
                    sales_growth = ((m1 - m2) / m2) * 100

        return MetricsSummary(
            totalSales=int(total_sales or 0),
            totalUsers=int(total_users or 0),
            revenue=float(revenue or 0.0),
            productsCount=int(products_count or 0),
            salesGrowth=round(sales_growth, 2),
            usersGrowth=0.0
        )
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")


class SaleItem(BaseModel):
    date: str
    product: str
    value: float
    quantity: int

@router.get("/recent-sales", response_model=list[SaleItem])
async def get_recent_sales(
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = 10
) -> list[SaleItem]:
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
             cols = rel.columns
        except Exception:
             return []
        
        # Usar nomes UPPERCASE do Parquet (padrão garantido)
        c_venda = "VENDA_30DD"
        c_nome = "NOME"
        c_produto = "PRODUTO"
        # Fallback date if updated_at missing
        c_updated = "updated_at" if "updated_at" in cols else "created_at"
        has_date = c_updated in cols

        # Query
        # If no date col, just take any rows
        query = f"SELECT {c_updated if has_date else 'NULL'} as dt, {c_nome}, {c_produto}, {c_venda} FROM recent WHERE {c_venda} > 0 LIMIT {limit}"
        
        results = rel.query("recent", query).fetchall()
        
        sales = []
        for r in results:
            dt, name, code, val = r
            product_display = str(name) if name else str(code)
            sales.append(SaleItem(
                date=str(dt) if dt else "N/A",
                product=product_display,
                value=float(val or 0.0),
                quantity=1
            ))
            
        return sales

    except Exception as e:
        logger.error(f"Error fetching recent sales: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching recent sales: {str(e)}")


class TopProduct(BaseModel):
    product: str
    productName: str
    totalSales: int
    revenue: float

@router.get("/top-products", response_model=list[TopProduct])
async def get_top_products(
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = 5
) -> list[TopProduct]:
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
             cols = rel.columns
        except Exception:
             return []
        
        # Usar nomes UPPERCASE do Parquet (padrão garantido)
        c_venda = "VENDA_30DD"
        c_produto = "PRODUTO"
        c_nome = "NOME"
        
        if c_venda not in cols:
            return []

        # Group By Logic
        grp_cols = [c_produto]
        sel_cols = [c_produto]
        if c_nome in cols:
            grp_cols.append(c_nome)
            sel_cols.append(c_nome)
            
        grp_sql = ", ".join(grp_cols)
        
        query = f"""
            SELECT {grp_sql}, SUM({c_venda}) as total_sales
            FROM top_prods
            WHERE {c_venda} > 0
            GROUP BY {grp_sql}
            ORDER BY total_sales DESC
            LIMIT {limit}
        """
        
        rows = rel.query("top_prods", query).fetchall()
        
        top_products = []
        for r in rows:
            # r could be (prod, sales) or (prod, name, sales)
            if len(r) == 3:
                prod, name, sales = r
            else:
                prod, sales = r
                name = prod
                
            top_products.append(TopProduct(
                product=str(prod),
                productName=str(name)[:50],
                totalSales=int(sales or 0),
                revenue=float(sales or 0) # Using sales as revenue proxy
            ))
            
        return top_products

    except Exception as e:
        logger.error(f"Error fetching top products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching top products: {str(e)}")


class BusinessKPIs(BaseModel):
    total_produtos: int
    total_unes: int
    produtos_ruptura: int
    valor_estoque: float
    top_produtos: list[dict]
    vendas_por_categoria: list[dict]


@router.get("/business-kpis", response_model=BusinessKPIs)
async def get_business_kpis(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> BusinessKPIs:
    """
    Get business KPIs using DuckDB
    """
    try:
        # Use configured connection for streaming
        conn = get_safe_connection()

        # Get lazy relation (True Streaming)
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)

        try:
             cols = rel.columns
        except Exception:
             return BusinessKPIs(total_produtos=0, total_unes=0, produtos_ruptura=0, valor_estoque=0.0, top_produtos=[], vendas_por_categoria=[])

        logger.info(f"Processing business KPIs (Streaming Mode)")

        def has(name): return name in cols

        # Usar nomes UPPERCASE do Parquet (padrão garantido)
        c_produto = "PRODUTO"
        c_une = "UNE"
        c_venda30 = "VENDA_30DD"

        # Stock columns
        c_est_une = "ESTOQUE_UNE" if has("ESTOQUE_UNE") else "0"
        c_est_cd = "ESTOQUE_CD" if has("ESTOQUE_CD") else "0"

        # 1. Scalar Metrics
        # rupture: %ABAST <= 50% (Guia UNE: ESTOQUE_UNE <= 50% LINHA_VERDE)
        rupture_expr = f"""SUM(CASE 
            WHEN TRY_CAST(ESTOQUE_LV AS DOUBLE) > 0 
             AND (TRY_CAST({c_est_une} AS DOUBLE) / TRY_CAST(ESTOQUE_LV AS DOUBLE)) <= 0.5
            THEN 1 ELSE 0 END)"""

        agg_sql = f"""
            SELECT
                COUNT(DISTINCT {c_produto}) as total_produtos,
                {f'COUNT(DISTINCT {c_une})' if c_une else '0'} as total_unes,
                COALESCE(SUM(TRY_CAST({c_est_une} AS DOUBLE) + TRY_CAST({c_est_cd} AS DOUBLE)), 0) as total_stock_val,
                {rupture_expr} as rupturas
            FROM metrics_kpi
        """

        metrics = rel.query("metrics_kpi", agg_sql).fetchone()
        tot_prod, tot_unes, val_stock, rupturas = metrics

        # 2. Top Products
        top_prod_list = []
        if has("PRODUTO"):
            c_nome = "NOME" if has("NOME") else c_produto
            top_sql = f"""
                SELECT {c_produto}, {c_nome}, SUM(TRY_CAST({c_venda30} AS DOUBLE)) as v
                FROM top_kpi
                WHERE TRY_CAST({c_venda30} AS DOUBLE) > 0
                GROUP BY {c_produto}, {c_nome}
                ORDER BY v DESC
                LIMIT 10
            """
            top_rows = rel.query("top_kpi", top_sql).fetchall()
            for r in top_rows:
                top_prod_list.append({
                    "produto": str(r[0]),
                    "nome": str(r[1])[:40],
                    "vendas": int(r[2])
                })

        # 3. Sales by Category
        cat_list = []
        cat_col = None
        for c in ["NOMEGRUPO", "NOMECATEGORIA", "NOMESEGMENTO"]:
            if has(c):
                cat_col = c
                break

        if cat_col:
            cat_sql = f"""
                SELECT {cat_col}, SUM(TRY_CAST({c_venda30} AS DOUBLE)) as v, COUNT(DISTINCT {c_produto}) as p
                FROM cats_kpi
                WHERE {cat_col} IS NOT NULL
                GROUP BY {cat_col}
                ORDER BY v DESC
                LIMIT 10
            """
            cat_rows = rel.query("cats_kpi", cat_sql).fetchall()
            for r in cat_rows:
                cat_list.append({
                    "categoria": str(r[0])[:30],
                    "vendas": int(r[1]),
                    "produtos": int(r[2])
                })

        return BusinessKPIs(
            total_produtos=int(tot_prod or 0),
            total_unes=int(tot_unes or 0),
            produtos_ruptura=int(rupturas or 0),
            valor_estoque=float(val_stock or 0.0),
            top_produtos=top_prod_list,
            vendas_por_categoria=cat_list
        )

    except Exception as e:
        logger.error(f"Error fetching business KPIs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching business KPIs: {str(e)}")


class KPIMetric(BaseModel):
    id: str
    title: str
    value: str | int | float
    change: float | None = None
    trend: str | None = None  # 'up', 'down', 'neutral'
    severity: str  # 'critical', 'warning', 'info', 'success'
    description: str
    action: str | None = None


class RealTimeKPIsResponse(BaseModel):
    critical_alerts: list[KPIMetric]
    performance: list[KPIMetric]
    opportunities: list[KPIMetric]
    generated_at: str
    calculation_time_ms: int


@router.get("/real-time-kpis", response_model=RealTimeKPIsResponse)
async def get_real_time_kpis(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> RealTimeKPIsResponse:
    """
    Real-time KPIs calculated with DuckDB (no LLM tokens consumed)
    Returns critical alerts, performance metrics, and business opportunities
    """
    import time
    from datetime import datetime

    start_time = time.time()

    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)

        try:
            cols = rel.columns
        except Exception:
            return RealTimeKPIsResponse(
                critical_alerts=[],
                performance=[],
                opportunities=[],
                generated_at=datetime.utcnow().isoformat(),
                calculation_time_ms=int((time.time() - start_time) * 1000)
            )

        logger.info("Calculating real-time KPIs with DuckDB")

        def has(name): return name in cols

        # Column mapping
        # Usar nomes UPPERCASE do Parquet (padrão garantido)
        c_produto = "PRODUTO"
        c_nome = "NOME"
        c_venda30 = "VENDA_30DD"
        c_est_une = "ESTOQUE_UNE"
        c_est_cd = "ESTOQUE_CD"
        # CORREÇÃO: PRECO_VENDA e PRECO_CUSTO não existem no Parquet
        c_preco = "LIQUIDO_38"  # Nome real para preço de venda
        c_custo = "ULTIMA_ENTRADA_CUSTO_CD"  # Nome real para custo

        critical_alerts = []
        performance = []
        opportunities = []

        # === CRITICAL ALERTS ===

        # 1. Rupturas - using %ABAST <= 50% (Guia UNE standard)
        rupture_sql = f"""
            SELECT COUNT(*) as count
            FROM rupture_check
            WHERE TRY_CAST(ESTOQUE_LV AS DOUBLE) > 0
            AND (TRY_CAST({c_est_une} AS DOUBLE) / TRY_CAST(ESTOQUE_LV AS DOUBLE)) <= 0.5
        """
        rupture_count = rel.query("rupture_check", rupture_sql).fetchone()[0]

        if rupture_count > 0:
            critical_alerts.append(KPIMetric(
                id="alert-ruptura",
                title="Produtos em Ruptura",
                value=rupture_count,
                severity="critical" if rupture_count > 50 else "warning",
                description=f"{rupture_count} produtos com abastecimento <= 50% da Linha Verde",
                action="Ver produtos em ruptura"
            ))

        # 2. Slow movers (estoque > 0, vendas = 0)
        slow_sql = f"""
            SELECT COUNT(*) as count
            FROM slow_check
            WHERE (TRY_CAST({c_est_une} AS DOUBLE) + TRY_CAST({c_est_cd} AS DOUBLE)) > 10
            AND TRY_CAST({c_venda30} AS DOUBLE) = 0
        """
        slow_count = rel.query("slow_check", slow_sql).fetchone()[0]

        if slow_count > 10:
            critical_alerts.append(KPIMetric(
                id="alert-slow",
                title="Produtos Parados",
                value=slow_count,
                severity="warning",
                description=f"{slow_count} produtos com estoque mas sem vendas",
                action="Avaliar desconto ou transferência"
            ))

        # === PERFORMANCE METRICS ===

        # 1. Fast movers (top velocity)
        fast_sql = f"""
            SELECT COUNT(*) as count, SUM(TRY_CAST({c_venda30} AS DOUBLE)) as total_sales
            FROM fast_check
            WHERE TRY_CAST({c_venda30} AS DOUBLE) > 100
        """
        fast_res = rel.query("fast_check", fast_sql).fetchone()
        fast_count, fast_sales = fast_res

        if fast_count > 0:
            performance.append(KPIMetric(
                id="perf-fast",
                title="High Velocity SKUs",
                value=fast_count,
                trend="up",
                severity="success",
                description=f"{fast_count} produtos com alta rotação (>100 vendas/30d)",
                action=None
            ))

        # 2. Stock coverage (days of inventory)
        coverage_sql = f"""
            SELECT
                AVG(CASE
                    WHEN TRY_CAST({c_venda30} AS DOUBLE) > 0
                    THEN (TRY_CAST({c_est_une} AS DOUBLE) + TRY_CAST({c_est_cd} AS DOUBLE)) / (TRY_CAST({c_venda30} AS DOUBLE) / 30.0)
                    ELSE NULL
                END) as avg_coverage
            FROM coverage_check
            WHERE TRY_CAST({c_venda30} AS DOUBLE) > 0
        """
        avg_coverage = rel.query("coverage_check", coverage_sql).fetchone()[0]

        if avg_coverage:
            coverage_days = int(avg_coverage)
            severity = "success" if coverage_days >= 15 else ("warning" if coverage_days >= 7 else "critical")
            performance.append(KPIMetric(
                id="perf-coverage",
                title="Cobertura Média",
                value=f"{coverage_days} dias",
                severity=severity,
                description=f"Estoque médio cobre {coverage_days} dias de vendas",
                trend="neutral" if coverage_days >= 15 else "down"
            ))

        # === OPPORTUNITIES ===

        # 1. High margin products
        if has(c_preco) and has(c_custo):
            margin_sql = f"""
                SELECT COUNT(*) as count, AVG((TRY_CAST({c_preco} AS DOUBLE) - TRY_CAST({c_custo} AS DOUBLE)) / NULLIF(TRY_CAST({c_preco} AS DOUBLE), 0) * 100) as avg_margin
                FROM margin_check
                WHERE TRY_CAST({c_preco} AS DOUBLE) > TRY_CAST({c_custo} AS DOUBLE)
                AND ((TRY_CAST({c_preco} AS DOUBLE) - TRY_CAST({c_custo} AS DOUBLE)) / NULLIF(TRY_CAST({c_preco} AS DOUBLE), 0)) > 0.4
                AND TRY_CAST({c_venda30} AS DOUBLE) > 0
            """
            margin_res = rel.query("margin_check", margin_sql).fetchone()
            margin_count, avg_margin = margin_res

            if margin_count and margin_count > 0:
                opportunities.append(KPIMetric(
                    id="opp-margin",
                    title="Produtos Alta Margem",
                    value=margin_count,
                    severity="success",
                    description=f"{margin_count} produtos com margem >40% vendendo ativamente",
                    action="Aumentar exposição destes produtos"
                ))

        # 2. Transfer opportunities
        transfer_sql = f"""
            SELECT COUNT(*) as count
            FROM transfer_check
            WHERE TRY_CAST({c_est_cd} AS DOUBLE) > 50
            AND TRY_CAST({c_est_une} AS DOUBLE) = 0
            AND TRY_CAST({c_venda30} AS DOUBLE) > 5
        """
        transfer_count = rel.query("transfer_check", transfer_sql).fetchone()[0]

        if transfer_count > 0:
            opportunities.append(KPIMetric(
                id="opp-transfer",
                title="Transferências Sugeridas",
                value=transfer_count,
                severity="info",
                description=f"{transfer_count} produtos com CD cheio e lojas zeradas vendendo",
                action="Gerar sugestões de transferência"
            ))

        # 3. Revenue potential (produtos vendendo com estoque baixo)
        potential_sql = f"""
            SELECT COUNT(*) as count, SUM(TRY_CAST({c_venda30} AS DOUBLE) * TRY_CAST({c_preco} AS DOUBLE)) as potential_revenue
            FROM potential_check
            WHERE TRY_CAST({c_venda30} AS DOUBLE) > 20
            AND (TRY_CAST({c_est_une} AS DOUBLE) + TRY_CAST({c_est_cd} AS DOUBLE)) < 10
        """
        potential_res = rel.query("potential_check", potential_sql).fetchone()
        potential_count, potential_revenue = potential_res

        if potential_count and potential_count > 0:
            opportunities.append(KPIMetric(
                id="opp-potential",
                title="Reposição Urgente",
                value=potential_count,
                severity="warning",
                description=f"{potential_count} produtos vendendo bem mas com estoque crítico",
                action="Priorizar reabastecimento"
            ))

        elapsed_ms = int((time.time() - start_time) * 1000)

        return RealTimeKPIsResponse(
            critical_alerts=critical_alerts,
            performance=performance,
            opportunities=opportunities,
            generated_at=datetime.utcnow().isoformat(),
            calculation_time_ms=elapsed_ms
        )

    except Exception as e:
        logger.error(f"Error calculating real-time KPIs: {str(e)}", exc_info=True)
        # Return empty response instead of error to avoid breaking dashboard
        return RealTimeKPIsResponse(
            critical_alerts=[],
            performance=[],
            opportunities=[],
            generated_at=datetime.utcnow().isoformat(),
            calculation_time_ms=int((time.time() - start_time) * 1000)
        )

