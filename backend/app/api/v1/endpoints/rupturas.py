from typing import Annotated, List, Dict, Any, Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query
import logging

from app.api.dependencies import get_current_active_user
from app.core.data_scope_service import data_scope_service
from app.infrastructure.database.models import User
from app.core.duckdb_config import get_safe_connection

router = APIRouter(prefix="/rupturas", tags=["Rupturas"])
logger = logging.getLogger(__name__)

@router.get("/critical", response_model=List[Dict[str, Any]])
async def get_critical_rupturas(
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(50, description="Número máximo de resultados"),
    segmento: Optional[str] = Query(None, description="Filtro por segmento (NOMESEGMENTO)"),
    une: Optional[str] = Query(None, description="Filtro por UNE")
):
    """
    Produtos com ruptura crítica (ESTOQUE_CD=0 + Estoque Loja < Linha Verde).
    Migrado para DuckDB.
    """
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
             cols = rel.columns
        except Exception:
             return []

        # Verificar colunas necessárias
        required_cols = ["ESTOQUE_CD", "ESTOQUE_UNE", "ESTOQUE_LV", "VENDA_30DD"]
        if not all(col in cols for col in required_cols):
            return []

        # Filters using Chaining (Safe & Lazy)
        if segmento and "NOMESEGMENTO" in cols:
            # Use f-string with proper escaping for DuckDB
            rel = rel.filter(f"NOMESEGMENTO = '{segmento}'")

        if une and "UNE" in cols:
            # Filter by UNE (integer or string)
            if str(une).isdigit():
                rel = rel.filter(f"UNE = {une}")
            else:
                rel = rel.filter(f"TRY_CAST(UNE AS VARCHAR) = '{une}'")

        # Core Logic Filters
        # Ruptura: CD<=0 AND UNE < LV AND VENDA > 0
        rel = rel.filter("COALESCE(TRY_CAST(ESTOQUE_CD AS DOUBLE), 0) <= 0")
        rel = rel.filter("COALESCE(TRY_CAST(ESTOQUE_UNE AS DOUBLE), 0) < COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0)")
        rel = rel.filter("COALESCE(TRY_CAST(VENDA_30DD AS DOUBLE), 0) > 0")

        # Calculations & Projection
        # Use SQL on the filtered relation
        sql = f"""
            SELECT *,
                -- CRITICIDADE: % de vendas vs capacidade
                CASE 
                    WHEN COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0) > 0 
                    THEN ROUND(LEAST(100, (COALESCE(TRY_CAST(VENDA_30DD AS DOUBLE), 0) / TRY_CAST(ESTOQUE_LV AS DOUBLE) * 100)), 2)
                    ELSE 0 
                END AS CRITICIDADE_PCT,
                
                -- NECESSIDADE: Quanto falta para atingir Linha Verde
                ROUND(GREATEST(0, COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0) - COALESCE(TRY_CAST(ESTOQUE_UNE AS DOUBLE), 0)), 2) AS NECESSIDADE,
                
                -- PERC_ABAST: % de abastecimento (EST_UNE / LV)
                CASE 
                    WHEN COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0) > 0 
                    THEN ROUND(COALESCE(TRY_CAST(ESTOQUE_UNE AS DOUBLE), 0) / TRY_CAST(ESTOQUE_LV AS DOUBLE) * 100, 2)
                    ELSE 0 
                END AS PERC_ABAST,
                
                -- A1: GATILHO_CRITICO: %ABAST <= 50%
                CASE 
                    WHEN COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0) > 0 
                     AND (COALESCE(TRY_CAST(ESTOQUE_UNE AS DOUBLE), 0) / TRY_CAST(ESTOQUE_LV AS DOUBLE)) <= 0.5
                    THEN 1 ELSE 0 
                END AS GATILHO_CRITICO,
                
                -- A2: FALHA_GATILHO: %ABAST <= 50% e sem disparo pendente
                CASE 
                    WHEN COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0) > 0 
                     AND (COALESCE(TRY_CAST(ESTOQUE_UNE AS DOUBLE), 0) / TRY_CAST(ESTOQUE_LV AS DOUBLE)) <= 0.5
                     AND COALESCE(TRY_CAST(SOLICITACAO_PENDENTE AS DOUBLE), 0) = 0
                    THEN 1 ELSE 0 
                END AS FALHA_GATILHO,
                
                -- A3: DEFICIT_PARAMETRO: MC > GONDOLA e TRAVA = SIM
                CASE 
                    WHEN COALESCE(TRY_CAST(MEDIA_CONSIDERADA_LV AS DOUBLE), 0) > COALESCE(TRY_CAST(ESTOQUE_GONDOLA_LV AS DOUBLE), 0)
                     AND UPPER(COALESCE(MEDIA_TRAVADA, '')) = 'SIM'
                    THEN 1 ELSE 0 
                END AS DEFICIT_PARAMETRO,
                
                -- C3: PISO_VIOLADO: LV < GONDOLA (regra de piso mínimo)
                CASE 
                    WHEN COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0) < COALESCE(TRY_CAST(ESTOQUE_GONDOLA_LV AS DOUBLE), 0)
                    THEN 1 ELSE 0 
                END AS PISO_VIOLADO
                
            FROM rupturas_criticas_view
            ORDER BY CRITICIDADE_PCT DESC, VENDA_30DD DESC
            LIMIT {limit}
        """

        res_rel = rel.query("rupturas_criticas_view", sql)
        col_names = res_rel.columns
        rows = res_rel.fetchall()

        # Map to dicts
        results = []
        for r in rows:
            results.append(dict(zip(col_names, r)))

        return results

    except Exception as e:
        logger.error(f"Error in critical rupturas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters/segmentos", response_model=List[str])
async def get_segmentos(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Lista todos os segmentos disponíveis para filtro.
    """
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
             cols = rel.columns
        except Exception:
             return []

        if "NOMESEGMENTO" not in cols:
            return []

        res = rel.select("NOMESEGMENTO").distinct().order("NOMESEGMENTO").fetchall()
        return [str(s[0]) for s in res if s[0] and str(s[0]).strip()]
    except Exception as e:
        logger.error(f"Error getting segmentos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters/unes", response_model=List[str])
async def get_unes(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Lista todas as UNEs disponíveis para filtro.
    """
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
             cols = rel.columns
        except Exception:
             return []

        if "UNE" not in cols:
            return []

        res = rel.select("UNE").distinct().order("UNE").fetchall()
        return [str(u[0]) for u in res if u[0] is not None]
    except Exception as e:
        logger.error(f"Error getting unes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=Dict[str, Any])
async def get_rupturas_summary(
    current_user: Annotated[User, Depends(get_current_active_user)],
    segmento: Optional[str] = Query(None, description="Filtro por segmento"),
    une: Optional[str] = Query(None, description="Filtro por UNE")
):
    """
    Retorna resumo de métricas de rupturas críticas.
    """
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
             cols = rel.columns
        except Exception:
             return {"total": 0, "criticos": 0, "valor_estimado": 0}

        required_cols = ["ESTOQUE_CD", "ESTOQUE_UNE", "ESTOQUE_LV", "VENDA_30DD"]
        if not all(col in cols for col in required_cols):
            return {"total": 0, "criticos": 0, "valor_estimado": 0}

        # Filters using Chaining
        if segmento and "NOMESEGMENTO" in cols:
            rel = rel.filter(f"NOMESEGMENTO = '{segmento}'")

        if une and "UNE" in cols:
            if str(une).isdigit():
                rel = rel.filter(f"UNE = {une}")
            else:
                rel = rel.filter(f"TRY_CAST(UNE AS VARCHAR) = '{une}'")

        # Core Logic Filters
        rel = rel.filter("COALESCE(TRY_CAST(ESTOQUE_CD AS DOUBLE), 0) <= 0")
        rel = rel.filter("COALESCE(TRY_CAST(ESTOQUE_UNE AS DOUBLE), 0) < COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0)")
        rel = rel.filter("COALESCE(TRY_CAST(VENDA_30DD AS DOUBLE), 0) > 0")

        # Count Query
        # Total rupturas match logic (already filtered in rel)
        # Criticos: Criticidade >= 75
        
        sql = f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE 
                    WHEN COALESCE(TRY_CAST(ESTOQUE_LV AS DOUBLE), 0) > 0 AND 
                         (COALESCE(TRY_CAST(VENDA_30DD AS DOUBLE), 0) / TRY_CAST(ESTOQUE_LV AS DOUBLE) * 100) >= 75 
                    THEN 1 ELSE 0 
                END) as criticos
            FROM rupturas_summary_view
        """
        
        res = rel.query("rupturas_summary_view", sql).fetchone()
        total, criticos = res

        return {
            "total": int(total or 0),
            "criticos": int(criticos or 0),
            "valor_estimado": 0 
        }
    except Exception as e:
        logger.error(f"Error in rupturas summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))