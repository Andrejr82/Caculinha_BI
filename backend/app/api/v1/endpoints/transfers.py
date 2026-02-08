from typing import Annotated, List, Dict, Any, Optional
from datetime import datetime
import json
import os
from pathlib import Path
import duckdb

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.app.api.dependencies import get_current_active_user
from backend.app.infrastructure.database.models import User
from backend.app.core.tools.une_tools import (
    validar_transferencia_produto,
    sugerir_transferencias_automaticas,
)
from backend.app.core.utils.error_handler import APIError
from backend.app.core.duckdb_config import get_safe_connection
from backend.app.core.data_scope_service import data_scope_service

router = APIRouter(prefix="/transfers", tags=["Transfers"])

# Path to store transfer requests
TRANSFER_REQUESTS_DIR = Path("data/transferencias")
os.makedirs(TRANSFER_REQUESTS_DIR, exist_ok=True)


class TransferRequestPayload(BaseModel):
    produto_id: int
    une_origem: int
    une_destino: int
    quantidade: int
    solicitante_id: str # Will be populated by current_user


class TransferReportQuery(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ProductSearchRequest(BaseModel):
    segmento: Optional[str] = None
    grupo: Optional[str] = None
    fabricante: Optional[str] = None
    estoque_min: Optional[int] = None
    limit: int = Field(default=50, le=500)


class BulkTransferRequestPayload(BaseModel):
    """Payload para transferências múltiplas (1→N ou N→N)"""
    items: List[TransferRequestPayload]
    modo: str = Field(description="Modo: '1→1', '1→N', ou 'N→N'")


@router.post("/validate")
async def validate_transfer(
    payload: TransferRequestPayload,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Dict[str, Any]:
    """
    Endpoint to validate a product transfer between UNEs.
    Integrates with `validar_transferencia_produto` tool.
    Includes priority score (0-100) and urgency level.
    """
    from backend.app.core.data_scope_service import data_scope_service

    try:
        # Validação básica usando a tool existente
        result = validar_transferencia_produto.invoke({
            "produto_id": payload.produto_id,
            "une_origem": payload.une_origem,
            "une_destino": payload.une_destino,
            "quantidade": payload.quantidade,
        })

        # Calcular score de prioridade baseado em criticidade
        score_prioridade = 50  # Default
        nivel_urgencia = "NORMAL"

        try:
            # Gets Lazy Relation
            conn = get_safe_connection()
            rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
            
            # Filter Relation
            # Filter: PRODUTO = ? AND UNE = ?
            # Casting IDs to correct types if needed.
            res = rel.filter("PRODUTO = $1 AND UNE = $2", 
                             str(payload.produto_id) if isinstance(payload.produto_id, str) else int(payload.produto_id), 
                             str(payload.une_destino) if isinstance(payload.une_destino, str) else int(payload.une_destino)
                             ).limit(1).fetchall()
            
            # Get columns from relation
            columns = rel.columns
            
            if res:
                row = dict(zip(columns, res[0]))

                estoque_loja = float(row.get("ESTOQUE_UNE") or 0)
                estoque_cd = float(row.get("ESTOQUE_CD") or 0)
                linha_verde = float(row.get("ESTOQUE_LV") or 0)
                venda_30dd = float(row.get("VENDA_30DD") or 0)

                # Calcular score (0-100)
                # Fatores: ruptura, vendas, relação estoque/linha verde
                score = 0

                # +40 pontos se CD zerado
                if estoque_cd == 0:
                    score += 40

                # +30 pontos se estoque loja < linha verde
                if estoque_loja < linha_verde:
                    score += 30

                # +20 pontos baseado em vendas (normalizado)
                if venda_30dd > 0:
                    score += min(20, int(venda_30dd / 10))

                # +10 pontos se estoque crítico (< 50% da LV)
                if linha_verde > 0 and estoque_loja < (linha_verde * 0.5):
                    score += 10

                score_prioridade = min(100, score)

                # Determinar nível de urgência
                if score_prioridade >= 80:
                    nivel_urgencia = "URGENTE"
                elif score_prioridade >= 60:
                    nivel_urgencia = "ALTA"
                elif score_prioridade >= 40:
                    nivel_urgencia = "MÉDIA"
                else:
                    nivel_urgencia = "BAIXA"
            # Connection managed by DuckDB (GC)

        except Exception as e:
            print(f"Erro ao calcular score: {e}")

        # Adicionar score ao resultado
        result["score_prioridade"] = score_prioridade
        result["nivel_urgencia"] = nivel_urgencia

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating transfer: {str(e)}",
        )


@router.get("/suggestions")
async def get_transfer_suggestions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    segmento: Optional[str] = Query(None),
    une_origem_excluir: Optional[int] = Query(None),
    limit: int = Query(5),
) -> List[Dict[str, Any]]:
    """
    Endpoint to get automatic transfer suggestions.
    Integrates with `sugerir_transferencias_automaticas` tool.
    """
    try:
        # Fix: Use .invoke() for LangChain StructuredTool
        suggestions = sugerir_transferencias_automaticas.invoke({
            "segmento": segmento,
            "une_origem_excluir": une_origem_excluir,
            "limite": limit
        })
        return suggestions if isinstance(suggestions, list) else []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting transfer suggestions: {str(e)}",
        )


@router.post("")
async def create_transfer_request(
    payload: TransferRequestPayload,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Dict[str, Any]:
    """
    Endpoint to create and save a transfer request.
    """
    try:
        transfer_data = payload.model_dump()
        transfer_data["solicitante_id"] = current_user.username
        transfer_data["timestamp"] = datetime.now().isoformat()
        transfer_id = f"transfer_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        file_path = TRANSFER_REQUESTS_DIR / f"{transfer_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(transfer_data, f, ensure_ascii=False, indent=4)

        return {"message": "Transfer request created successfully", "transfer_id": transfer_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transfer request: {str(e)}",
        )


@router.get("/report")
async def get_transfers_report(
    current_user: Annotated[User, Depends(get_current_active_user)],
    query: TransferReportQuery = Depends(),
) -> List[Dict[str, Any]]:
    """
    Endpoint to generate a report of transfer requests.
    Reads JSON files from the `data/transferencias/` directory.
    """
    all_transfers = []
    start_date = datetime.fromisoformat(query.start_date) if query.start_date else datetime.min
    end_date = datetime.fromisoformat(query.end_date) if query.end_date else datetime.max

    for filename in os.listdir(TRANSFER_REQUESTS_DIR):
        if filename.endswith(".json"):
            file_path = TRANSFER_REQUESTS_DIR / filename
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    transfer_data = json.load(f)
                    transfer_timestamp = datetime.fromisoformat(transfer_data.get("timestamp"))
                    if start_date <= transfer_timestamp <= end_date:
                        all_transfers.append(transfer_data)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error reading or decoding transfer file {file_path}: {e}")
                # Optionally, raise HTTPException if corrupt file is critical

    # Basic aggregation or sorting could be done here if needed
    all_transfers.sort(key=lambda x: x.get("timestamp"), reverse=True)

    return all_transfers


@router.get("/filters")
async def get_transfer_filters(
    current_user: Annotated[User, Depends(get_current_active_user)],
    segmento: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Endpoint to get available filter options for transfers.
    Returns unique values for segmento, grupo and fabricante.
    Implements cascading logic: Segment -> Group -> Manufacturer.
    """
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)

        # Determinar nomes corretos das colunas
        try:
             cols = rel.columns
        except:
             return {"segmentos": [], "grupos": [], "fabricantes": []}

        segmento_col = "NOMESEGMENTO" if "NOMESEGMENTO" in cols else None
        grupo_col = "NOMEGRUPO" if "NOMEGRUPO" in cols else None
        fabricante_col = "NOMEFABRICANTE" if "NOMEFABRICANTE" in cols else None

        # Helper to get distinct list
        def get_distinct(relation, col_name, filter_conditions=None):
            if not col_name: return []
            curr = relation
            if filter_conditions:
                for col, val in filter_conditions.items():
                    if val and col in cols:
                         # FIX: Use f-string interpolation for filter instead of binding
                         # Check for SQL injection here if input wasn't internal/validated, 
                         # but for internal known columns and query params it's generally safe in this context or sanitize.
                         # Since these are values from DB, simple quote escaping is usually enough.
                         safe_val = str(val).replace("'", "''")
                         curr = curr.filter(f"{col} = '{safe_val}'")
            
            res = curr.select(col_name).distinct().order(col_name).fetchall()
            return [str(r[0]) for r in res if r[0] and str(r[0]).strip()]

        # 1. Segmentos (Always full list or filtered by user scope only)
        segmentos = get_distinct(rel, segmento_col)

        # 2. Grupos (Filtered by Segmento)
        grupos_filters = {}
        if segmento and segmento_col:
            grupos_filters[segmento_col] = segmento
        grupos = get_distinct(rel, grupo_col, grupos_filters)

        # 3. Fabricantes (Filtered by Segmento AND Grupo)
        fab_filters = {}
        if segmento and segmento_col:
            fab_filters[segmento_col] = segmento
        if grupo and grupo_col:
            fab_filters[grupo_col] = grupo
            
        fabricantes = get_distinct(rel, fabricante_col, fab_filters)
            
        return {
            "segmentos": segmentos, 
            "grupos": grupos,
            "fabricantes": fabricantes
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting filters: {str(e)}",
        )


@router.post("/products/search")
async def search_products(
    request: ProductSearchRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[Dict[str, Any]]:
    """
    Endpoint to search products with filters for transfer management.
    Returns products matching criteria with stock information.
    """
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)
        
        try:
             cols = rel.columns
        except:
             return []

        # Determinar nomes corretos das colunas
        segmento_col = "NOMESEGMENTO" if "NOMESEGMENTO" in cols else None
        grupo_col = "NOMEGRUPO" if "NOMEGRUPO" in cols else None
        fabricante_col = "NOMEFABRICANTE" if "NOMEFABRICANTE" in cols else None

        # Construir filtros Chaining
        # FIX: Explicit f-string interpolation for LIKE/ILIKE patterns 
        # to avoid "incompatible function arguments" error in current DuckDB python binding
        if request.segmento and segmento_col:
             # Sanitize input to prevent injection
             safe_seg = request.segmento.replace("'", "''")
             rel = rel.filter(f"{segmento_col} ILIKE '%{safe_seg}%'")

        if request.grupo and grupo_col:
             safe_grp = request.grupo.replace("'", "''")
             rel = rel.filter(f"{grupo_col} ILIKE '%{safe_grp}%'")

        if request.fabricante and fabricante_col:
             safe_fab = request.fabricante.replace("'", "''")
             rel = rel.filter(f"{fabricante_col} ILIKE '%{safe_fab}%'")

        if request.estoque_min is not None:
             rel = rel.filter(f"COALESCE(TRY_CAST(ESTOQUE_UNE AS DOUBLE), 0) >= {request.estoque_min}")

        # Preparar colunas para agrupamento
        grp_fields = ["PRODUTO", "NOME"]
        if segmento_col: grp_fields.append(segmento_col)
        if grupo_col: grp_fields.append(grupo_col)
        if fabricante_col: grp_fields.append(fabricante_col)
        
        # Select expressions
        seg_sel = f"{segmento_col} as segmento" if segmento_col else "'N/A' as segmento"
        grp_sel = f"{grupo_col} as grupo" if grupo_col else "'N/A' as grupo"
        fab_sel = f"{fabricante_col} as fabricante" if fabricante_col else "'N/A' as fabricante"
        
        grp_sql = ", ".join(grp_fields)

        query = f"""
            SELECT 
                PRODUTO as produto_id,
                NOME as nome,
                {seg_sel},
                {grp_sel},
                {fab_sel},
                COALESCE(SUM(TRY_CAST(ESTOQUE_UNE AS DOUBLE)), 0) as estoque_total_loja,
                COALESCE(SUM(TRY_CAST(ESTOQUE_CD AS DOUBLE)), 0) as estoque_total_cd,
                COALESCE(SUM(TRY_CAST(VENDA_30DD AS DOUBLE)), 0) as vendas_30dd,
                COUNT(DISTINCT UNE) as unes_com_estoque
            FROM search_prods
            GROUP BY {grp_sql}
            LIMIT {request.limit}
        """

        res_rel = rel.query("search_prods", query)
        res = res_rel.fetchall()
        cols_res = res_rel.columns
        
        products = []
        for r in res:
             row = dict(zip(cols_res, r))
             products.append({
                 "produto_id": int(row["produto_id"]),
                 "nome": str(row["nome"])[:60],
                 "segmento": str(row["segmento"]),
                 "grupo": str(row["grupo"]),
                 "fabricante": str(row["fabricante"])[:30],
                 "estoque_loja": int(row["estoque_total_loja"]),
                 "estoque_cd": int(row["estoque_total_cd"]),
                 "vendas_30dd": int(row["vendas_30dd"]),
                 "unes": int(row["unes_com_estoque"])
             })
        
        return products

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching products: {str(e)}",
        )


@router.post("/bulk")
async def create_bulk_transfer_request(
    payload: BulkTransferRequestPayload,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Dict[str, Any]:
    """
    Endpoint to create multiple transfer requests at once (1→N or N→N modes).
    Saves all transfers in a single batch file.
    """
    try:
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        batch_data = {
            "batch_id": batch_id,
            "modo": payload.modo,
            "solicitante_id": current_user.username,
            "timestamp": datetime.now().isoformat(),
            "total_transferencias": len(payload.items),
            "transferencias": []
        }

        for item in payload.items:
            transfer = item.model_dump()
            transfer["solicitante_id"] = current_user.username
            batch_data["transferencias"].append(transfer)

        file_path = TRANSFER_REQUESTS_DIR / f"{batch_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=4)

        return {
            "message": f"Batch transfer request created successfully ({len(payload.items)} items)",
            "batch_id": batch_id,
            "modo": payload.modo
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bulk transfer request: {str(e)}",
        )


@router.get("/unes")
async def get_available_unes(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[Dict[str, Any]]:
    """
    Endpoint to get list of available UNEs for transfer selection.
    """
    try:
        conn = get_safe_connection()
        rel = data_scope_service.get_filtered_dataframe(current_user, conn=conn)

        # Obter UNEs únicas com contagem de produtos
        # Use SQL on relation
        query = """
            SELECT 
                UNE as une,
                COUNT(DISTINCT PRODUTO) as total_produtos,
                COALESCE(SUM(TRY_CAST(ESTOQUE_UNE AS DOUBLE)), 0) as estoque_total
            FROM unes_list
            GROUP BY UNE
            ORDER BY UNE
        """
        
        res_rel = rel.query("unes_list", query)
        res = res_rel.fetchall()
        cols_res = res_rel.columns

        unes = []
        for r in res:
            row = dict(zip(cols_res, r))
            unes.append({
                "une": int(row["une"]),
                "total_produtos": int(row["total_produtos"]),
                "estoque_total": int(row["estoque_total"])
            })
        
        return unes

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching UNEs: {str(e)}",
        )
