"""
Dashboard Endpoints - API para Dashboards Forecasting, Executive e Suppliers
Conecta diretamente com admmat.parquet para fornecer dados em tempo real.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
import duckdb
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
from backend.app.api.dependencies import get_current_active_user
from backend.app.core.context import set_current_user_context
from backend.app.infrastructure.database.models import User

print("DEBUG: LOADING DASHBOARD MODULE (WITH EXPORT ENDPOINT)!!!")

# [OK] FIX: Removed direct import to break circular dependency
# from app.core.tools.purchasing_tools import calcular_eoq, prever_demanda_sazonal
# Tools will be imported lazily inside functions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Path to parquet file
PARQUET_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "parquet" / "admmat.parquet"


def get_parquet_path() -> str:
    """Resolve o caminho do arquivo parquet."""
    possible_paths = [
        PARQUET_PATH,
        Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "parquet" / "admmat.parquet",
        Path(__file__).parent.parent.parent.parent / "data" / "parquet" / "admmat.parquet",
    ]
    
    for p in possible_paths:
        if p.exists():
            return str(p).replace("\\", "/")
    
    raise FileNotFoundError("admmat.parquet não encontrado")



def _execute_duckdb_query(sql: str) -> pd.DataFrame:
    """Executa query SQL usando DuckDB e retorna DataFrame."""
    try:
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        # Substituir 'data' pelo caminho do parquet
        sql_adjusted = sql.replace("FROM data", f"FROM read_parquet('{parquet_path}')")
        sql_adjusted = sql_adjusted.replace("from data", f"FROM read_parquet('{parquet_path}')")
        
        result = con.execute(sql_adjusted).fetchdf()
        con.close()
        return result
    except Exception as e:
        logger.error(f"Erro ao executar query DuckDB: {e}")
        return pd.DataFrame()





# ============================================================================

# ============================================================================
# SCHEMAS
# ============================================================================

class ForecastRequest(BaseModel):
    produto_id: str
    periodo_dias: int = 30
    considerar_sazonalidade: bool = True
    une: Optional[str] = None # Filtro opcional por loja


class EOQRequest(BaseModel):
    produto_id: str


class AllocationRequest(BaseModel):
    produto_id: str
    quantidade_total: int
    criterio: str = "prioridade_ruptura"


class ExecutiveKPIs(BaseModel):
    vendas_total: float
    vendas_variacao: float
    margem_media: float
    margem_variacao: float
    taxa_ruptura: float
    ruptura_variacao: float
    produtos_ativos: int
    produtos_variacao: float


class Alert(BaseModel):
    type: str  # critical, warning, info
    message: str
    timestamp: str


class Supplier(BaseModel):
    nome: str
    lead_time_medio: float
    taxa_ruptura: float
    custo_medio: float
    produtos_fornecidos: int
    ultima_entrega: str


# TOOLS ENDPOINTS (para Forecasting)
# ============================================================================

@router.post("/tools/prever_demanda")
async def api_prever_demanda(request: ForecastRequest):
    """Endpoint para previsão de demanda (com ajuste sazonal opcional)."""
    try:
        # [OK] FIX: Lazy import to avoid circular dependency
        from backend.app.core.tools.purchasing_tools import calculate_demand_forecast_logic
        
        result = calculate_demand_forecast_logic(
            produto_id=request.produto_id,
            periodo_dias=request.periodo_dias,
            considerar_sazonalidade=request.considerar_sazonalidade,
            une=request.une
        )
        return result
    except Exception as e:
        logger.error(f"Erro ao prever demanda: {e}")
        return {"error": str(e)}

# ============================================================================
# METADATA ENDPOINTS
# ============================================================================

@router.get("/metadata/segments")
async def list_segments():
    """List distinct segments for filtering."""
    try:
        query = "SELECT DISTINCT TRIM(NOMESEGMENTO) as SEGMENTO FROM data WHERE NOMESEGMENTO IS NOT NULL ORDER BY 1"
        df = _execute_duckdb_query(query)
        if df.empty: return []
        return df['SEGMENTO'].tolist()
    except Exception as e:
        return []

@router.get("/metadata/stores")
async def list_stores():
    """List distinct stores (UNEs) for filtering."""
    try:
        # Pega as lojas que realmente têm vendas (Agrupado por UNE para evitar duplicatas de nomes variantes)
        query = "SELECT UNE, MAX(TRIM(UNE_NOME)) as NOME FROM data WHERE UNE IS NOT NULL GROUP BY UNE ORDER BY UNE"
        df = _execute_duckdb_query(query)
        if df.empty: return []
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Erro ao listar lojas: {e}")
        return []

@router.get("/metadata/groups")
async def list_groups(segmento: str):
    """List distinct groups (NOMEGRUPO) for a given segment."""
    try:
        if not segmento:
            return []
            
        segmento_clean = segmento.replace("'", "''")
        
        # FIX: Use NOMEGRUPO instead of CATEGORIA
        query = f"SELECT DISTINCT TRIM(NOMEGRUPO) as GRUPO FROM data WHERE NOMESEGMENTO = '{segmento_clean}' AND NOMEGRUPO IS NOT NULL ORDER BY 1"
        df = _execute_duckdb_query(query)
        if df.empty: return []
        return df['GRUPO'].tolist()
    except Exception as e:
        logger.error(f"Erro ao listar grupos: {e}")
        return []



@router.post("/tools/calcular_eoq")
async def api_calcular_eoq(request: EOQRequest):
    """Endpoint para cálculo de EOQ."""
    try:
        # [OK] FIX: Lazy import to avoid circular dependency
        from backend.app.core.tools.purchasing_tools import calculate_eoq_logic
        
        result = calculate_eoq_logic(produto_id=request.produto_id)
        return result
    except Exception as e:
        logger.error(f"Erro ao calcular EOQ: {e}")
        return {"error": str(e)}


class AllocationRequest(BaseModel):
    produto_id: str
    quantidade_total: int
    criterio: str = "prioridade_ruptura"


@router.post("/tools/alocar_estoque")
async def api_alocar_estoque(request: AllocationRequest):
    """Endpoint para sugestão de alocação de estoque entre lojas."""
    try:
        # [OK] FIX: Lazy import to avoid circular dependency
        from backend.app.core.tools.purchasing_tools import allocate_stock_logic
        
        result = allocate_stock_logic(
            produto_id=request.produto_id,
            quantidade_total=request.quantidade_total,
            criterio=request.criterio
        )
        return result
    except Exception as e:
        logger.error(f"Erro ao alocar estoque: {e}")
        return {"error": str(e)}


# ============================================================================
# EXECUTIVE DASHBOARD ENDPOINTS
# ============================================================================

# ============================================================================
# EXECUTIVE DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/metrics/executive-kpis")
async def get_executive_kpis(current_user: User = Depends(get_current_active_user)):
    """Retorna KPIs executivos do dashboard com RLS."""
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        where = "WHERE TRY_CAST(LIQUIDO_38 AS DOUBLE) > 0"
        
        # RLS Logic
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            safe = [s.replace("'", "''") for s in allowed]
            sql_in = ",".join([f"'{s}'" for s in safe])
            where += f" AND NOMESEGMENTO IN ({sql_in})"
        
        # Query para KPIs
        query = f"""
            SELECT 
                COALESCE(SUM(TRY_CAST(VENDA_30DD AS DOUBLE) * TRY_CAST(LIQUIDO_38 AS DOUBLE)), 0) as vendas_total,
                COALESCE(AVG(
                    (TRY_CAST(LIQUIDO_38 AS DOUBLE) - TRY_CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE)) 
                    / NULLIF(TRY_CAST(LIQUIDO_38 AS DOUBLE), 0)
                ) * 100, 0) as margem_media,
                COUNT(DISTINCT PRODUTO) as produtos_ativos
            FROM read_parquet('{parquet_path}')
            {where}
        """
        
        result = con.execute(query).fetchone()
        con.close()
        
        vendas_total = float(result[0]) if result[0] else 0
        margem_media = float(result[1]) if result[1] else 0
        produtos_ativos = int(result[2]) if result[2] else 0
        
        # Query para ruptura (produtos sem estoque)
        con = duckdb.connect()
        # RLS for Ruptura
        where_ruptura = ""
        if allowed and "*" not in allowed:
            safe = [s.replace("'", "''") for s in allowed]
            sql_in = ",".join([f"'{s}'" for s in safe])
            where_ruptura = f"WHERE NOMESEGMENTO IN ({sql_in})"
            
        ruptura_query = f"""
            SELECT 
                COUNT(CASE WHEN TRY_CAST(ESTOQUE_UNE AS DOUBLE) <= 0 THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0) as taxa_ruptura
            FROM read_parquet('{parquet_path}')
            {where_ruptura}
        """
        ruptura_result = con.execute(ruptura_query).fetchone()
        con.close()
        
        taxa_ruptura = float(ruptura_result[0]) if ruptura_result[0] else 0
        
        return {
            "vendas_total": vendas_total,
            "vendas_variacao": 0.0,
            "margem_media": margem_media,
            "margem_variacao": 0.0,
            "taxa_ruptura": taxa_ruptura,
            "ruptura_variacao": 0.0,
            "produtos_ativos": produtos_ativos,
            "produtos_variacao": 0.0
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar KPIs: {e}")
        return {
            "vendas_total": 0,
            "vendas_variacao": 0,
            "margem_media": 0,
            "margem_variacao": 0,
            "taxa_ruptura": 0,
            "ruptura_variacao": 0,
            "produtos_ativos": 0,
            "produtos_variacao": 0
        }


@router.get("/alerts/critical")
async def get_critical_alerts(current_user: User = Depends(get_current_active_user)):
    """Retorna alertas críticos do sistema com RLS."""
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        where = "WHERE TRY_CAST(ESTOQUE_UNE AS DOUBLE) <= 0 AND TRY_CAST(VENDA_30DD AS DOUBLE) > 0"
        
        # RLS Logic
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            safe = [s.replace("'", "''") for s in allowed]
            sql_in = ",".join([f"'{s}'" for s in safe])
            where += f" AND NOMESEGMENTO IN ({sql_in})"
        
        query = f"""
            SELECT 
                PRODUTO,
                NOME as DESCRICAO,
                TRY_CAST(ESTOQUE_UNE AS DOUBLE) as ESTOQUE_ATUAL,
                TRY_CAST(VENDA_30DD AS DOUBLE) as VENDA_30DIAS
            FROM read_parquet('{parquet_path}')
            {where}
            ORDER BY VENDA_30DIAS DESC
            LIMIT 5
        """
        
        results = con.execute(query).fetchall()
        con.close()
        
        alerts = []
        for row in results:
            alerts.append({
                "type": "critical",
                "message": f"Ruptura: {row[1]} (Cód: {row[0]}) - Vendas 30d: {row[3]:.0f}",
                "timestamp": datetime.now().isoformat()
            })
        
        return {"alerts": alerts}
        
    except Exception as e:
        logger.error(f"Erro ao buscar alertas: {e}")
        return {"alerts": []}


@router.get("/top-vendidos")
async def get_top_vendidos(current_user: User = Depends(get_current_active_user)):
    """Retorna top 50 produtos mais vendidos com RLS."""
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        where = "WHERE TRY_CAST(VENDA_30DD AS DOUBLE) > 0"
        
        # RLS Logic
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            safe = [s.replace("'", "''") for s in allowed]
            sql_in = ",".join([f"'{s}'" for s in safe])
            where += f" AND NOMESEGMENTO IN ({sql_in})"
        
        query = f"""
            SELECT 
                PRODUTO,
                NOME as DESCRICAO,
                SUM(TRY_CAST(VENDA_30DD AS DOUBLE)) as total_vendas,
                SUM(TRY_CAST(LIQUIDO_38 AS DOUBLE)) as faturamento,
                AVG(
                    (TRY_CAST(LIQUIDO_38 AS DOUBLE) - TRY_CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE)) 
                    / NULLIF(TRY_CAST(LIQUIDO_38 AS DOUBLE), 0)
                ) * 100 as margem_percent,
                TRY_CAST(ESTOQUE_UNE AS DOUBLE) as estoque,
                UNE,
                MAX(UNE_NOME) as loja_nome
            FROM read_parquet('{parquet_path}')
            {where}
            GROUP BY PRODUTO, NOME, ESTOQUE_UNE, UNE
            ORDER BY total_vendas DESC
            LIMIT 50
        """
        
        results = con.execute(query).fetchall()
        con.close()
        
        return {
            "produtos": [
                {
                    "produto": row[0],
                    "descricao": str(row[1])[:40],
                    "vendas": int(row[2] or 0),
                    "faturamento": float(row[3] or 0),
                    "margem": float(row[4] or 0),
                    "estoque": int(row[5] or 0),
                    "une": int(row[6] or 0),
                    "loja": str(row[7] or "")
                }
                for row in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar top vendidos: {e}")
        return {"produtos": []}


@router.get("/top-margin")
async def get_top_margin_products(current_user: User = Depends(get_current_active_user)):
    """
    Retorna top 50 produtos com maior margem (R$) com RLS.
    """
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        where = "WHERE TRY_CAST(VENDA_30DD AS DOUBLE) > 5 AND TRY_CAST(LIQUIDO_38 AS DOUBLE) > 0"
        
        # RLS Logic
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            safe = [s.replace("'", "''") for s in allowed]
            sql_in = ",".join([f"'{s}'" for s in safe])
            where += f" AND NOMESEGMENTO IN ({sql_in})"
        
        query = f"""
            SELECT 
                PRODUTO,
                NOME as DESCRICAO,
                TRY_CAST(VENDA_30DD AS DOUBLE) as vendas,
                (TRY_CAST(LIQUIDO_38 AS DOUBLE) - TRY_CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE)) as margem_reais,
                (
                    (TRY_CAST(LIQUIDO_38 AS DOUBLE) - TRY_CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE)) 
                    / NULLIF(TRY_CAST(LIQUIDO_38 AS DOUBLE), 0)
                ) * 100 as margem_percent,
                TRY_CAST(ESTOQUE_UNE AS DOUBLE) as estoque,
                UNE,
                UNE_NOME as loja_nome
            FROM read_parquet('{parquet_path}')
            {where}
            ORDER BY margem_percent DESC
            LIMIT 50
        """
        
        results = con.execute(query).fetchall()
        con.close()
        
        return {
            "produtos": [
                {
                    "produto": row[0],
                    "descricao": str(row[1])[:40],
                    "vendas": int(row[2] or 0),
                    "margem_reais": float(row[3] or 0),
                    "margem": float(row[4] or 0),
                    "estoque": int(row[5] or 0),
                    "une": int(row[6] or 0),
                    "loja": str(row[7] or "")
                }
                for row in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar top margem: {e}")
        return {"produtos": []}



from backend.app.api.dependencies import get_current_active_user
from backend.app.core.context import set_current_user_context
from backend.app.infrastructure.database.models import User

# ============================================================================
# METADATA ENDPOINTS (Filters)
# ============================================================================

@router.get("/metadata/segments")
async def get_segments(current_user: User = Depends(get_current_active_user)):
    """Retorna lista única de segmentos com RLS aplicado."""
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        where = "WHERE NOMESEGMENTO IS NOT NULL"
        
        # RLS Logic
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            safe = [s.replace("'", "''") for s in allowed]
            sql_in = ",".join([f"'{s}'" for s in safe])
            where += f" AND NOMESEGMENTO IN ({sql_in})"
            
        query = f"SELECT DISTINCT NOMESEGMENTO FROM read_parquet('{parquet_path}') {where} ORDER BY 1"
        result = con.execute(query).fetchall()
        return [r[0] for r in result]
    except Exception as e:
        logger.error(f"Erro ao buscar segmentos: {e}")
        return []

@router.get("/metadata/groups")
async def get_groups(segmento: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    """Retorna lista única de grupos (opcionalmente filtrados por segmento) com RLS."""
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        where = "WHERE NOMEGRUPO IS NOT NULL"
        if segmento:
            seg_clean = segmento.replace("'", "''")
            where += f" AND NOMESEGMENTO = '{seg_clean}'"
            
        # RLS Logic
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            safe = [s.replace("'", "''") for s in allowed]
            sql_in = ",".join([f"'{s}'" for s in safe])
            where += f" AND NOMESEGMENTO IN ({sql_in})"
            
        query = f"SELECT DISTINCT NOMEGRUPO FROM read_parquet('{parquet_path}') {where} ORDER BY 1"
        result = con.execute(query).fetchall()
        return [r[0] for r in result]
    except Exception as e:
        logger.error(f"Erro ao buscar grupos: {e}")
        return []


# ============================================================================
# SUPPLIERS DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/suppliers/metrics")
async def get_suppliers_metrics(current_user: User = Depends(get_current_active_user)):
    """Retorna métricas de fornecedores com RLS."""
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        where_clause = "WHERE NOMESEGMENTO IS NOT NULL AND TRIM(NOMESEGMENTO) != '' AND NOMESEGMENTO != 'nan'"
        
        # RLS Logic
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            safe = [s.replace("'", "''") for s in allowed]
            sql_in = ",".join([f"'{s}'" for s in safe])
            where_clause += f" AND NOMESEGMENTO IN ({sql_in})"
        
        query = f"""
            SELECT 
                NOMESEGMENTO as nome,
                0 as lead_time_medio,
                COUNT(CASE WHEN TRY_CAST(ESTOQUE_UNE AS DOUBLE) <= 0 THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(*), 0) as taxa_ruptura,
                AVG(COALESCE(TRY_CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE), 0)) as custo_medio,
                COUNT(DISTINCT PRODUTO) as produtos_fornecidos,
                '' as ultima_entrega
            FROM read_parquet('{parquet_path}')
            {where_clause}
            GROUP BY NOMESEGMENTO
            ORDER BY taxa_ruptura DESC
            LIMIT 20
        """
        
        results = con.execute(query).fetchall()
        columns = [desc[0] for desc in con.description]
        con.close()
        
        suppliers = []
        for row in results:
            row_dict = dict(zip(columns, row))
            suppliers.append({
                "nome": row_dict["nome"],
                "lead_time_medio": float(row_dict["lead_time_medio"]) if row_dict["lead_time_medio"] else 0,
                "taxa_ruptura": float(row_dict["taxa_ruptura"]) if row_dict["taxa_ruptura"] else 0,
                "custo_medio": float(row_dict["custo_medio"]) if row_dict["custo_medio"] else 0,
                "produtos_fornecidos": int(row_dict["produtos_fornecidos"]) if row_dict["produtos_fornecidos"] else 0,
                "ultima_entrega": str(row_dict["ultima_entrega"]) if row_dict["ultima_entrega"] else ""
            })
        
        return {"suppliers": suppliers}
        
    except Exception as e:
        logger.error(f"Erro ao buscar fornecedores: {e}")
        return {"suppliers": []}


# DEPRECATED DUPLICATE: @router.get("/metadata/segments") REMOVED (Already defined above)


@router.get("/suppliers/groups")
async def get_groups_by_segment(segmento: str, current_user: User = Depends(get_current_active_user)):
    """Retorna grupos de produtos dentro de um segmento específico com RLS."""
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        if not segmento:
            return {"groups": [], "error": "Segmento não informado"}
            
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        # RLS Check: User can only access requested segment if allowed
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            if segmento not in allowed:
                return {"groups": [], "error": "Acesso negado a este segmento"}
        
        query = f"""
            SELECT 
                COALESCE(TRIM(NOMEGRUPO), 'SEM GRUPO') as grupo,
                TRIM(NOMESEGMENTO) as segmento,
                COUNT(CASE WHEN TRY_CAST(ESTOQUE_UNE AS DOUBLE) <= 0 THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(*), 0) as taxa_ruptura,
                AVG(COALESCE(TRY_CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE), 0)) as custo_medio,
                COUNT(DISTINCT PRODUTO) as produtos,
                SUM(COALESCE(TRY_CAST(ESTOQUE_UNE AS DOUBLE), 0)) as estoque_total,
                SUM(COALESCE(TRY_CAST(VENDA_30DD AS DOUBLE), 0)) as vendas_30d
            FROM read_parquet('{parquet_path}')
            WHERE TRIM(NOMESEGMENTO) = '{segmento.replace("'", "''")}'
            GROUP BY NOMEGRUPO, NOMESEGMENTO
            ORDER BY taxa_ruptura DESC
            LIMIT 100
        """
        
        results = con.execute(query).fetchall()
        columns = [desc[0] for desc in con.description]
        con.close()
        
        groups = []
        for row in results:
            row_dict = dict(zip(columns, row))
            groups.append({
                "grupo": row_dict["grupo"] or "SEM GRUPO",
                "segmento": row_dict["segmento"],
                "taxa_ruptura": float(row_dict["taxa_ruptura"]) if row_dict["taxa_ruptura"] else 0,
                "custo_medio": float(row_dict["custo_medio"]) if row_dict["custo_medio"] else 0,
                "produtos": int(row_dict["produtos"]) if row_dict["produtos"] else 0,
                "estoque_total": float(row_dict["estoque_total"]) if row_dict["estoque_total"] else 0,
                "vendas_30d": float(row_dict["vendas_30d"]) if row_dict["vendas_30d"] else 0
            })
        
        return {"groups": groups, "segmento": segmento, "total": len(groups)}
        
    except Exception as e:
        logger.error(f"Erro ao buscar grupos do segmento {segmento}: {e}")
        return {"groups": [], "error": str(e)}


@router.get("/products/list")
async def get_products_by_filter(segmento: str, grupo: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    """
    Retorna lista de produtos para o painel de previsão (Master-Detail) com RLS.
    """
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        # RLS Check
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            if segmento not in allowed:
                return {"products": [], "error": "Acesso negado a este segmento"}
        
        # Filtros
        seg_safe = segmento.replace("'", "''")
        where_clause = f"TRIM(NOMESEGMENTO) = '{seg_safe}'"
        
        if grupo and grupo != "SEM GRUPO":
            grp_safe = grupo.replace("'", "''")
            where_clause += f" AND TRIM(NOMEGRUPO) = '{grp_safe}'"
            
        query = f"""
            SELECT 
                PRODUTO as id,
                TRIM(NOME) as nome,
                TRY_CAST(VENDA_30DD AS DOUBLE) as venda_30d,
                TRY_CAST(ESTOQUE_UNE AS DOUBLE) as estoque,
                CASE 
                    WHEN TRY_CAST(VENDA_30DD AS DOUBLE) > 0 
                    THEN TRY_CAST(ESTOQUE_UNE AS DOUBLE) / (TRY_CAST(VENDA_30DD AS DOUBLE) / 30)
                    ELSE 999 
                END as dias_cobertura
            FROM read_parquet('{parquet_path}')
            WHERE {where_clause}
            ORDER BY dias_cobertura ASC, venda_30d DESC
            LIMIT 100
        """
        
        results = con.execute(query).fetchall()
        columns = [desc[0] for desc in con.description]
        con.close()
        
        products = []
        for row in results:
            r = dict(zip(columns, row))
            products.append({
                "id": str(r["id"]),
                "nome": r["nome"],
                "venda_30d": float(r["venda_30d"]) if r["venda_30d"] else 0,
                "estoque": float(r["estoque"]) if r["estoque"] else 0,
                "dias_cobertura": float(r["dias_cobertura"]) if r["dias_cobertura"] else 999
            })
            
        return {"products": products}
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos para o segmento {segmento}: {e}")
        return {"products": [], "error": str(e)}


@router.get("/suppliers/export_ruptures")
async def export_ruptures_csv(segmento: str, grupo: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    """
    Gera um CSV com produtos em ruptura (Estoque <= 0) para o segmento/grupo com RLS.
    """
    try:
        set_current_user_context(current_user)
        from backend.app.core.context import get_current_user_segments
        
        parquet_path = get_parquet_path()
        con = duckdb.connect()
        
        # RLS Check
        allowed = get_current_user_segments()
        if allowed and "*" not in allowed:
            if segmento not in allowed:
                raise HTTPException(status_code=403, detail="Acesso negado a este segmento")
        
        # Filtros (Sanitização básica de SQL Injection manual)
        seg_safe = segmento.replace("'", "''")
        where_clause = f"TRIM(NOMESEGMENTO) = '{seg_safe}'"
        
        if grupo and grupo != "SEM GRUPO":
            grp_safe = grupo.replace("'", "''")
            where_clause += f" AND TRIM(NOMEGRUPO) = '{grp_safe}'"
        elif grupo == "SEM GRUPO":
             where_clause += " AND (NOMEGRUPO IS NULL OR TRIM(NOMEGRUPO) = '')"
            
        where_clause += " AND TRY_CAST(ESTOQUE_UNE AS DOUBLE) <= 0"
        
        query = f"""
            SELECT 
                PRODUTO as CODIGO,
                TRIM(NOME) as PRODUTO,
                TRIM(UNE_NOME) as UN,
                TRIM(NOMEGRUPO) as GRUPO,
                TRY_CAST(VENDA_30DD AS DOUBLE) as VENDA_30D,
                TRY_CAST(ULTIMA_ENTRADA_CUSTO_CD AS DOUBLE) as CUSTO,
                TRY_CAST(ESTOQUE_UNE AS DOUBLE) as ESTOQUE_ATUAL
            FROM read_parquet('{parquet_path}')
            WHERE {where_clause}
            ORDER BY VENDA_30D DESC NULLS LAST
            LIMIT 5000
        """
        
        df = con.execute(query).fetchdf()
        con.close()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Nenhum produto em ruptura encontrado para os filtros selecionados.")
            
        # Converter para CSV
        import io
        from fastapi.responses import StreamingResponse
        
        stream = io.StringIO()
        df.to_csv(stream, index=False, sep=";")
        
        filename = f"rupturas_{segmento}"
        if grupo:
            filename += f"_{grupo}"
        filename = filename.replace(" ", "_").lower() + ".csv"
        
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao exportar rupturas: {e}")
        # Retorna erro JSON se falhar antes do stream
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

