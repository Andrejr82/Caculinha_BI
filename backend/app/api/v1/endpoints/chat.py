"""
Chat Endpoints
BI Chat with AI assistant
"""

from typing import Annotated, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import ORJSONResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
import json
import asyncio
import logging
import sys
import re
from urllib.parse import urlparse
import numpy as np
import pandas as pd
from decimal import Decimal
from datetime import datetime, date

# Import core dependencies
from backend.app.api.dependencies import get_current_active_user, get_token_from_header_or_query, issue_stream_token
from backend.app.infrastructure.database.models import User
from backend.app.config.settings import settings
from backend.app.core.utils.response_cache import ResponseCache
from backend.app.core.utils.query_history import QueryHistory
from backend.app.core.utils.field_mapper import FieldMapper
from backend.app.core.rag.query_retriever import QueryRetriever
from backend.app.core.learning.pattern_matcher import PatternMatcher
# CodeGenAgent e CaculinhaBIAgent removidos - Arquitetura V2 deprecated
# Sistema agora usa ChatServiceV3 (Metrics-First)
from backend.app.core.llm_factory import LLMFactory, SmartLLM
from backend.app.core.utils.error_handler import APIError
from backend.app.core.utils.session_manager import SessionManager
from backend.app.core.utils.semantic_cache import cache_get, cache_set, cache_stats
from backend.app.core.utils.response_validator import validate_response, validator_stats
# NEW SERVICE V3 - Metrics-First Architecture
from backend.app.services.chat_service_v3 import ChatServiceV3
from backend.services.metrics import MetricsService
try:
    from backend.app.core.tools.competitive_intelligence_tool import pesquisar_precos_concorrentes
    from backend.app.core.tools.competitive_intelligence_tool import pesquisar_mercado_web
except (ImportError, OSError):
    pesquisar_precos_concorrentes = None
    pesquisar_mercado_web = None

logger = logging.getLogger(__name__)

def _is_degraded_or_error_response(payload: Any) -> bool:
    """Avoid caching degraded/error messages and ignore them on cache reads."""
    text = str(payload).lower()
    degraded_markers = [
        "tempo limite",
        "quota estourada",
        "resource_exhausted",
        "serviço de ia temporariamente indisponível",
        "payload too large",
        "request too large",
        "erro ao processar",
        "busca externa não foi concluída nesta rodada",
        "nenhuma evidência pública validada",
    ]
    return any(marker in text for marker in degraded_markers)


def _sanitize_business_output(text: str) -> str:
    """Remove technical/internal leakage from final user-visible answer."""
    if not text:
        return text

    cleaned = str(text)
    blocked_patterns = [
        r"(?i)\bbase\s*=\s*[a-z0-9_.-]+",
        r"(?i)\b(parquet|duckdb|schema|coluna[s]?\s+internas?|tabela[s]?\s+internas?)\b",
        # Bloqueia caminhos de filesystem, mas preserva rotas web (ex.: /api/v1/...).
        r"(?i)\b[a-z]:\\[^\s]+",
        r"(?i)/(?:home|users?|usr|var|opt|etc|tmp|mnt|srv|root|proc|sys|dev|workspace|projects?|repos?)/[^\s]+",
        r"(?i)\b(venda_30dd|estoque_une|liquido_38|nomesegmento)\b",
    ]
    for pattern in blocked_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _is_competitive_market_query(query: str) -> bool:
    q = (query or "").lower()
    markers = [
        "concorrente", "concorrência", "cotação", "cotacao",
        "pesquisa de preço", "pesquisa de preco",
        "pesquisa de mercado", "preço de mercado", "preco de mercado",
        "benchmark de mercado", "pesquisa concorrencial",
        "comparar preço", "comparar preco",
        "americanas", "kalunga", "bellart", "shopee", "amazon", "mercado livre",
        "google shopping",
    ]
    return any(m in q for m in markers)


def _has_specific_competitor(query: str) -> bool:
    """Retorna True se a query menciona um concorrente específico pelo nome."""
    q = (query or "").lower()
    competitors = [
        "americanas", "kalunga", "bellart", "shopee", "amazon",
        "casa&video", "casa e video", "le biscuit", "lebiscuit",
        "tubarão", "tubarao", "tid", "amigão", "amigao",
    ]
    return any(c in q for c in competitors)


def _extract_market_product_hint(query: str) -> str:
    q = (query or "").strip()
    if not q:
        return "item solicitado"

    lowered = q.lower()
    lowered = re.sub(r"^(faca|faça|faz|fazer)\s+(uma\s+)?", "", lowered)
    lowered = re.sub(r"^(realize|realizar|realiza)\s+(uma\s+)?", "", lowered)
    lowered = re.sub(r"^(pesquisa|pesquise|compare|comparar|benchmark)\s+", "", lowered)
    lowered = re.sub(r"^(de\s+mercado|de\s+pre[çc]o)\s+", "", lowered)
    lowered = re.sub(r"^(do|da|de|o|a)?\s*produto\s+", "", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip(" .,-")
    return lowered or "item solicitado"


def _competitive_timeout_business_message(query: str) -> str:
    produto = _extract_market_product_hint(query)
    return (
        "## Resumo executivo\n"
        f"- A busca de mercado para {produto} foi concluída parcialmente nesta rodada.\n"
        "- Não houve evidência pública suficiente para consolidar preço confiável agora.\n\n"
        "## Ação recomendada\n"
        "- Use cotação direta com 2-3 fornecedores para decisão imediata.\n"
        "- Refaça a pesquisa com SKU/marca e especificação completa para ampliar cobertura.\n\n"
        "## Próxima consulta sugerida\n"
        f"- \"pesquisa de mercado de {produto} marca X, medida Y, em RJ\""
        "\n\n## Status\n"
        "- Busca externa não foi concluída nesta rodada."
    )


def _extract_market_state(query: str) -> str:
    q = (query or "").lower()
    if re.search(r"\b(rj|rio de janeiro)\b", q):
        return "RJ"
    if re.search(r"\b(mg|minas gerais)\b", q):
        return "MG"
    if re.search(r"\b(es|esp[ií]rito santo|espirito santo)\b", q):
        return "ES"
    return "RJ"


def _extract_market_competitors_csv(query: str) -> str:
    q = (query or "").lower()
    mapping = [
        ("americanas", ["americanas", "lojas americanas"]),
        ("kalunga", ["kalunga"]),
        ("bellart", ["bellart"]),
        ("amazon", ["amazon"]),
        ("shopee", ["shopee"]),
        ("mercado livre", ["mercado livre", "mercadolivre", "meli"]),
        ("casa&video", ["casa&video", "casa e video", "casaevideo"]),
        ("le biscuit", ["le biscuit", "lebiscuit"]),
    ]
    found = []
    for canonical, aliases in mapping:
        if any(alias in q for alias in aliases):
            found.append(canonical)
    return ",".join(found)


def _price_to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    txt = str(value).strip()
    if not txt:
        return None
    txt = txt.replace("R$", "").replace(" ", "")
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return None


def _format_brl(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _business_source_label(item: Dict[str, Any]) -> str:
    url = str(item.get("url") or "").strip()
    if url:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        if domain:
            return domain
    fonte = str(item.get("fonte") or "").strip().lower()
    if fonte in {"manual", "benchmark_seed_local", "base_manual_concorrencial", "csv_compras"}:
        return ""
    return fonte or "fonte_publica"


def _is_public_price_evidence(item: Dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False
    price = _price_to_float(item.get("preco"))
    if price is None:
        return False
    url = str(item.get("url") or "").strip()
    if not url:
        return False
    source = str(item.get("fonte") or "").strip().lower()
    if source in {"manual", "benchmark_seed_local", "base_manual_concorrencial", "csv_compras"}:
        return False
    domain = urlparse(url).netloc.lower().replace("www.", "")
    if not domain or domain == "manual":
        return False
    return True


# ---------------------------------------------------------------------------
# Preço interno do parquet + cache de resultados para download
# ---------------------------------------------------------------------------
import io
import tempfile
from uuid import uuid4 as _uuid4

# Cache simples em memória: {search_id: {"rows": [...], "produto": str, "internal_price": {...}, "created_at": str}}
_market_search_cache: Dict[str, Dict[str, Any]] = {}


def _lookup_internal_price(product_hint: str) -> Dict[str, Any]:
    """Busca preço de venda (LIQUIDO_38) e custo (ULTIMA_ENTRADA_CUSTO_CD) no parquet."""
    try:
        import duckdb
        parquet_path = str(Path(settings.PARQUET_DATA_PATH).resolve())
        if not Path(parquet_path).exists():
            # Tentar caminho relativo ao backend
            parquet_path = str(Path(__file__).resolve().parent.parent.parent.parent / settings.PARQUET_DATA_PATH)
        if not Path(parquet_path).exists():
            return {}

        terms = product_hint.lower().split()
        where_parts = []
        for term in terms[:4]:  # Máximo 4 termos
            safe_term = term.replace("'", "''")
            where_parts.append(f"LOWER(NOME) LIKE '%{safe_term}%'")

        if not where_parts:
            return {}

        where_clause = " AND ".join(where_parts)
        sql = (
            f"SELECT NOME, LIQUIDO_38, ULTIMA_ENTRADA_CUSTO_CD "
            f"FROM read_parquet('{parquet_path}') "
            f"WHERE {where_clause} "
            f"AND LIQUIDO_38 > 0 "
            f"LIMIT 5"
        )
        conn = duckdb.connect()
        result = conn.execute(sql).fetchall()
        conn.close()

        if not result:
            return {}

        # Pegar a média dos preços encontrados
        precos_venda = [float(r[1]) for r in result if r[1] and float(r[1]) > 0]
        custos = [float(r[2]) for r in result if r[2] and float(r[2]) > 0]
        nomes = [str(r[0]) for r in result]

        return {
            "preco_venda": round(sum(precos_venda) / len(precos_venda), 2) if precos_venda else None,
            "custo": round(sum(custos) / len(custos), 2) if custos else None,
            "produtos_encontrados": len(result),
            "nome_exemplo": nomes[0] if nomes else None,
        }
    except Exception as e:
        logger.warning(f"Erro ao buscar preço interno: {e}")
        return {}


def _competitive_no_evidence_business_message(query: str) -> str:
    produto = _extract_market_product_hint(query)
    return (
        "## Resumo executivo\n"
        f"- Nao encontrei nenhuma evidência pública validada para {produto} nesta consulta.\n\n"
        "## Como obter resultado mais preciso\n"
        "- Informe marca, gramatura/medida e embalagem (ex.: \"TNT branco 40g rolo 1,40m x 50m\").\n"
        "- Se quiser, inclua concorrente e estado (ex.: Kalunga em RJ).\n\n"
        "## Proxima consulta sugerida\n"
        f"- \"pesquisa de mercado de {produto} marca X medida Y em RJ\""
    )


def _build_competitive_structured_business_message(query: str, payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        return _competitive_no_evidence_business_message(query)

    raw_items = payload.get("itens") or []
    if not isinstance(raw_items, list):
        raw_items = []

    valid_items = [item for item in raw_items if _is_public_price_evidence(item)]
    if not valid_items:
        return _competitive_no_evidence_business_message(query)

    rows = []
    for item in valid_items:
        price = _price_to_float(item.get("preco"))
        if price is None:
            continue
        rows.append(
            {
                "concorrente": str(item.get("concorrente") or "concorrente").strip(),
                "produto": str(item.get("produto") or "produto").strip(),
                "preco": price,
                "fonte": _business_source_label(item),
            }
        )

    if not rows:
        return _competitive_no_evidence_business_message(query)

    rows = sorted(rows, key=lambda r: r["preco"])
    avg_price = sum(r["preco"] for r in rows) / len(rows)
    min_row = rows[0]
    max_row = rows[-1]

    # Buscar preço interno
    produto = _extract_market_product_hint(query)
    internal = _lookup_internal_price(produto)

    # Salvar no cache para download posterior
    search_id = str(_uuid4())[:8]
    _market_search_cache[search_id] = {
        "rows": rows,
        "produto": produto,
        "internal_price": internal,
        "avg_price": avg_price,
        "created_at": datetime.now().isoformat(),
    }
    # Limpar cache antigo (manter apenas últimos 20)
    if len(_market_search_cache) > 20:
        oldest_key = next(iter(_market_search_cache))
        _market_search_cache.pop(oldest_key, None)

    table_lines = [
        "| Concorrente | Produto | Preco (R$) | Fonte |",
        "|---|---|---:|---|",
    ]
    for row in rows[:15]:
        table_lines.append(
            f"| {row['concorrente']} | {row['produto'][:60]} | {_format_brl(row['preco'])} | {row['fonte'] or 'site'} |"
        )

    # Montar seção de preço interno
    internal_section = ""
    acao_interna = ""
    if internal.get("preco_venda"):
        pv = internal["preco_venda"]
        custo = internal.get("custo")
        diff_pct = ((pv - avg_price) / avg_price) * 100 if avg_price > 0 else 0
        position = "ACIMA" if diff_pct > 0 else "ABAIXO"

        internal_section = f"- Nosso preco de venda: R$ {_format_brl(pv)}"
        if custo:
            internal_section += f" | Nosso custo: R$ {_format_brl(custo)}"
        internal_section += "\n"
        
        acao_interna = f"- Nosso preco esta {abs(diff_pct):.0f}% {position} da media de mercado (R$ {_format_brl(pv)} vs R$ {_format_brl(avg_price)}).\n"
        if custo:
            margem = ((pv - custo) / pv) * 100 if pv > 0 else 0
            acao_interna += f"- Margem estimada: {margem:.0f}% sobre custo.\n"

    # Links relativos para funcionar em qualquer ambiente (dev/prod) via mesmo host do frontend.
    download_section = (
        f"\n## Download dos resultados\n"
        f"- [Baixar Excel (.xlsx)](/api/v1/chat/market-research/download/{search_id}?format=xlsx)\n"
        f"- [Baixar CSV (.csv)](/api/v1/chat/market-research/download/{search_id}?format=csv)\n"
    )

    return (
        "## Resumo executivo\n"
        + f"- Pesquisa de mercado concluida para **{produto}** com {len(rows)} referencias.\n"
        + (f"{internal_section}" if internal_section else "")
        + f"- Preco medio de mercado: R$ {_format_brl(avg_price)}\n"
        + f"- Faixa: R$ {_format_brl(min_row['preco'])} ate R$ {_format_brl(max_row['preco'])}\n"
        + "## Tabela operacional\n"
        + "\n".join(table_lines)
        + "\n\n## Acao recomendada\n"
        + (
            f"- Use a faixa entre R$ {_format_brl(min_row['preco'])} e R$ {_format_brl(avg_price)} como referencia de negociacao.\n"
            if not internal.get("preco_venda")
            else acao_interna
        )
        + download_section
    )

async def _run_competitive_market_fast_path(query: str) -> str:
    if pesquisar_precos_concorrentes is None:
        return _competitive_no_evidence_business_message(query)

    estado = _extract_market_state(query)
    concorrentes_csv = _extract_market_competitors_csv(query)

    def _invoke_tool() -> Any:
        tool_input = {
            "descricao_produto": query,
            "segmento": "",
            "estado": estado,
            "cidade": "",
            "limite": "12",
            "concorrentes": concorrentes_csv,
        }
        if hasattr(pesquisar_precos_concorrentes, "invoke"):
            return pesquisar_precos_concorrentes.invoke(tool_input)
        return pesquisar_precos_concorrentes(**tool_input)

    try:
        raw = await asyncio.wait_for(asyncio.to_thread(_invoke_tool), timeout=55.0)
    except asyncio.TimeoutError:
        logger.warning("Competitive fast-path timeout para query: %s", query)
        return _competitive_no_evidence_business_message(query)
    except Exception as exc:
        logger.error("Competitive fast-path error: %s", exc, exc_info=True)
        return _competitive_no_evidence_business_message(query)

    payload: Dict[str, Any]
    if isinstance(raw, dict):
        payload = raw
    elif isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            payload = parsed if isinstance(parsed, dict) else {"status": "error"}
        except Exception:
            payload = {"status": "error"}
    else:
        payload = {"status": "error"}

    return _build_competitive_structured_business_message(query, payload)


async def _run_market_research_fast_path(query: str) -> str:
    """Fast path para pesquisa de mercado genérica usando pesquisar_mercado_web."""
    if pesquisar_mercado_web is None:
        return _competitive_no_evidence_business_message(query)

    produto = _extract_market_product_hint(query)

    def _invoke_tool() -> Any:
        fn = getattr(pesquisar_mercado_web, "func", pesquisar_mercado_web)
        return fn(termo_pesquisa=produto, limite="15")

    try:
        raw = await asyncio.wait_for(asyncio.to_thread(_invoke_tool), timeout=55.0)
    except asyncio.TimeoutError:
        logger.warning("Market research fast-path timeout para query: %s", query)
        return _competitive_no_evidence_business_message(query)
    except Exception as exc:
        logger.error("Market research fast-path error: %s", exc, exc_info=True)
        return _competitive_no_evidence_business_message(query)

    payload: Dict[str, Any]
    if isinstance(raw, dict):
        payload = raw
    elif isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            payload = parsed if isinstance(parsed, dict) else {"status": "error"}
        except Exception:
            payload = {"status": "error"}
    else:
        payload = {"status": "error"}

    return _build_competitive_structured_business_message(query, payload)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    Safely serialize any Python object to JSON string.
    Handles MapComposite, numpy types, pandas types, datetime, and other non-serializable objects.
    """
    def default_handler(o):
        # Handle numpy types
        if isinstance(o, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(o)
        elif isinstance(o, (np.floating, np.float64, np.float32, np.float16)):
            if np.isnan(o) or np.isinf(o):
                return None
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()
        elif isinstance(o, np.bool_):
            return bool(o)

        # Handle pandas types
        elif isinstance(o, pd.Timestamp):
            return o.isoformat()
        elif isinstance(o, pd.Timedelta):
            return str(o)
        elif pd.isna(o):
            return None

        # Handle datetime types
        elif isinstance(o, (datetime, date)):
            return o.isoformat()

        # Handle Decimal
        elif isinstance(o, Decimal):
            return float(o)

        # Handle bytes
        elif isinstance(o, bytes):
            return o.decode('utf-8', errors='ignore')

        # Handle SQLAlchemy Row/MapComposite and similar mapping types
        elif hasattr(o, '_mapping'):
            return dict(o._mapping)
        elif hasattr(o, '__dict__') and not isinstance(o, type):
            # Generic object with __dict__
            return {k: v for k, v in o.__dict__.items() if not k.startswith('_')}

        # Last resort: convert to string
        else:
            return str(o)

    try:
        # Merge default handler with any custom kwargs
        if 'default' not in kwargs:
            kwargs['default'] = default_handler
        return json.dumps(obj, **kwargs)
    except Exception as e:
        logger.error(f"Failed to serialize object: {e}", exc_info=True)
        # Ultimate fallback: return error as JSON
        return json.dumps({"error": f"Serialization failed: {str(e)}"}, ensure_ascii=False)


# [OK] PERFORMANCE FIX: Initialization moved to startup background task
# This prevents the 15s delay on the first user query.
chat_service_v3 = None  # Metrics-First Architecture
session_manager = None
query_history = None  # [OK] FIX: Added missing variable for feedback endpoint
_init_lock = asyncio.Lock()
_CHAT_CACHE_VERSION = "chatbi_v3_20260218_r3"

# [OK] FIX: Import os for feedback endpoint
import os

async def initialize_agents_async():
    """
    Async initialization: Executed on app startup (background task).
    Ensures ChatService is ready when the user arrives.
    """
    global chat_service_v3, session_manager
    
    # Fast exit if already initialized
    if chat_service_v3 is not None:
        return

    async with _init_lock:
        if chat_service_v3 is not None:
            return
            
        logger.info("[START] [STARTUP] Initializing ChatServiceV3 (Metrics-First) in background...")
        
        try:
            # We must use asyncio.to_thread because initialization involves
            # heavy sync operations (loading vector stores, DuckDB connections)
            def _sync_init():
                import sys
                print("[DEBUG] [TRAP] Entering _sync_init...", file=sys.stderr)
                try:
                    print("[DEBUG] [TRAP] Init SessionManager...", file=sys.stderr)
                    local_session_manager = SessionManager(storage_dir="app/data/sessions")
                    
                    print("[DEBUG] [TRAP] Init ChatServiceV3...", file=sys.stderr)
                    local_service = ChatServiceV3(session_manager=local_session_manager)
                    
                    print("[DEBUG] [TRAP] ChatServiceV3 Success!", file=sys.stderr)
                    return local_session_manager, local_service
                except Exception as e:
                    import traceback
                    print(f"[ERROR] [TRAP] CRASH IN _sync_init: {e}", file=sys.stderr)
                    traceback.print_exc()
                    raise e
                    
            session_manager, chat_service_v3 = await asyncio.to_thread(_sync_init)
            
            logger.info("[OK] [STARTUP] ChatServiceV3 (Metrics-First) initialized successfully.")
        except Exception as e:
            import sys
            print(f"[ERROR] [TRAP] Async Init Failed: {e}", file=sys.stderr)
            logger.error(f"[ERROR] Failed to initialize ChatServiceV3: {e}", exc_info=True)
            # We don't raise here to avoid crashing the whole app, 
            # but Chat endpoints will fail if this didn't work.

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    query: str


class FeedbackRequest(BaseModel):
    response_id: str
    feedback_type: str
    comment: Optional[str] = None


class ChatResponse(BaseModel):
    response: str


@router.get("/market-research/download/{search_id}")
async def download_market_results(
    search_id: str,
    format: str = "xlsx"
):
    """
    Exporta os resultados da pesquisa de mercado para Excel ou CSV.
    """
    if search_id not in _market_search_cache:
        raise HTTPException(status_code=404, detail="Resultados da pesquisa não encontrados ou expirados.")

    data = _market_search_cache[search_id]
    rows = data["rows"]
    produto = data["produto"]
    internal = data.get("internal_price", {})

    output = io.BytesIO()
    
    if format.lower() == "xlsx":
        import openpyxl
        from openpyxl.styles import Font, Alignment
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Pesquisa de Mercado"
        
        # Cabeçalho
        headers = ["Concorrente", "Produto", "Preço (R$)", "Fonte"]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
            
        # Dados
        for row in rows:
            ws.append([
                row["concorrente"],
                row["produto"],
                row["preco"],
                row["fonte"]
            ])
            
        # Adicionar Preço Interno se disponível
        if internal.get("preco_venda"):
            ws.append([])
            ws.append(["--- INFORMAÇÕES INTERNAS ---"])
            ws.append(["Nosso Preço de Venda", internal["preco_venda"]])
            ws.append(["Nosso Custo", internal.get("custo")])
            ws.append(["Mídia de Mercado", data.get("avg_price")])
            
        wb.save(output)
        output.seek(0)
        
        filename = f"pesquisa_mercado_{search_id}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
    else: # Default to CSV
        import csv
        content = io.StringIO()
        writer = csv.writer(content, delimiter=";", lineterminator="\n")
        
        writer.writerow(["Concorrente", "Produto", "Preco", "Fonte"])
        for row in rows:
            writer.writerow([
                row["concorrente"],
                row["produto"],
                f"{row['preco']:.2f}".replace(".", ","),
                row["fonte"]
            ])
            
        if internal.get("preco_venda"):
            writer.writerow([])
            writer.writerow(["--- INFORMACOES INTERNAS ---"])
            writer.writerow(["Nosso Preco de Venda", f"{internal['preco_venda']:.2f}".replace(".", ",")])
            writer.writerow(["Nosso Custo", f"{internal.get('custo', 0):.2f}".replace(".", ",")])
            
        output.write(content.getvalue().encode("utf-8-sig"))
        output.seek(0)
        
        filename = f"pesquisa_mercado_{search_id}.csv"
        media_type = "text/csv"

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/stream-token")
async def create_stream_token(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Emite token efêmero para SSE, evitando expor JWT completo na URL.
    TTL curto e uso único.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization Bearer ausente")

    bearer = auth_header[7:].strip()
    if not bearer:
        raise HTTPException(status_code=401, detail="Token inválido")

    ephemeral = issue_stream_token(bearer)
    return {"stream_token": ephemeral, "expires_in": 120}


@router.get("/llm/status")
async def llm_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Status operacional dos provedores LLM configurados para o ChatBI.
    """
    global chat_service_v3
    if chat_service_v3 is None:
        await initialize_agents_async()
    if chat_service_v3 is None:
        raise HTTPException(status_code=503, detail="Chat service ainda não inicializado")
    return chat_service_v3.get_llm_status()


@router.get("/context7/status")
async def context7_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Status operacional da integração Context7 externa (quando configurada).
    """
    from backend.app.core.integrations.context7_status import get_context7_status

    return get_context7_status()


@router.get("/stream")
async def stream_chat(
    q: str,
    session_id: str,
    request: Request,
    token: Annotated[str, Depends(get_token_from_header_or_query)],
):
    """
    Streaming endpoint using Server-Sent Events (SSE)
    Integrates the agent system for dynamic responses.
    """
    from backend.app.api.dependencies import get_current_user_from_token
    from backend.app.core.context import set_current_user_context

    try:
        current_user = await get_current_user_from_token(token)
        # [OK] CRITICAL FIX: Set context for tools running in background
        set_current_user_context(current_user)
        logger.info(f"SSE authenticated user: {current_user.username}")
    except Exception as e:
        logger.error(f"SSE authentication failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Sessao invalida ou expirada. Faca login novamente."},
        )

    last_event_id = request.headers.get("Last-Event-ID")
    logger.info(f"==> SSE STREAM REQUEST: {q} (Session: {session_id}) (Last-Event-ID: {last_event_id}) <==")

    async def event_generator():
        final_sent = False
        try:
            event_counter = int(last_event_id) if last_event_id else 0

            # --- FAST PATH: Detecção de Saudações Simples (Zero Latency) ---
            # EXTREMAMENTE CRÍTICO: Deve rodar ANTES de qualquer inicialização pesada (initialize_agents_async)
            query_clean = q.strip().lower()
            greetings = [
                "oi", "ola", "olá", "bom dia", "boa tarde", "boa noite",
                "hello", "hi", "eai", "opa", "teste", "funcionando?", "tá funcionando", "ta funcionando",
                "tudo bem", "como vai", "e aí"
            ]

            # [OK] FIX 2026-01-14: Aumentado limite de 20 para 40 caracteres
            # "ola boa tarde tudo bem" tem 21 chars e não entrava no fast path
            # [OK] FIX 2026-01-17: Lógica refinada para não interceptar queries reais
            # Só interceptar se for APENAS saudação ou saudação curta SEM verbos de ação
            action_keywords = [
                "analis", "venda", "estoque", "ruptura", "grafico", "relatorio", 
                "quanto", "quais", "mostre", "gere", "crie", "veja", "dados"
            ]
            has_action = any(k in query_clean for k in action_keywords)
            
            is_pure_greeting = query_clean in greetings
            # Reduzido de 40 para 20 caracteres para evitar falsos positivos
            is_short_greeting = len(query_clean) < 20 and any(g in query_clean for g in greetings)

            if (is_pure_greeting or is_short_greeting) and not has_action:
                import random
                import asyncio
                from datetime import datetime

                # [OK] FIX 2026-01-15: Responder com saudação apropriada ao período
                # Detecta período mencionado pelo usuário ou usa hora atual
                if "boa noite" in query_clean:
                    saudacao = "Boa noite"
                elif "boa tarde" in query_clean:
                    saudacao = "Boa tarde"
                elif "bom dia" in query_clean:
                    saudacao = "Bom dia"
                else:
                    # Usa hora atual do servidor
                    hora = datetime.now().hour
                    if 5 <= hora < 12:
                        saudacao = "Bom dia"
                    elif 12 <= hora < 18:
                        saudacao = "Boa tarde"
                    else:
                        saudacao = "Boa noite"

                responses = [
                    f"{saudacao}! Sou seu assistente de BI. Como posso ajudar com os dados hoje?",
                    f"{saudacao}! Tudo pronto para analisar seus dados. O que você gostaria de ver?",
                    f"{saudacao}! Estou à disposição. Pode me pedir gráficos, relatórios ou análises.",
                    f"{saudacao}! Vamos encontrar alguns insights? É só perguntar."
                ]
                response_text = random.choice(responses)
                
                # Simular steps de progresso para UX consistente
                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'tool_progress', 'tool': 'system.thinking', 'status': 'start'})}\n\n"
                
                await asyncio.sleep(0.1) 
                
                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'tool_progress', 'tool': 'system.finalizing', 'status': 'finishing'})}\n\n"

                # Stream response text
                words = response_text.split(" ")
                for i in range(0, len(words), 3):
                    chunk_words = words[i:i + 3]
                    prefix = " " if i > 0 else ""
                    chunk_text = prefix + " ".join(chunk_words)
                    event_counter += 1
                    yield f"id: {event_counter}\n"
                    yield f"data: {safe_json_dumps({'type': 'text', 'text': chunk_text, 'done': False})}\n\n"
                    await asyncio.sleep(0.05) # Typing effect

                # Finalize
                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'final', 'text': '', 'done': True})}\n\n"
                final_sent = True
                return # SAÍDA ANTECIPADA - Evita carregar o agente pesado

            # --- FAST PATH: pesquisa concorrencial/mercado direta (sem pipeline completo do agente) ---
            if _is_competitive_market_query(query_clean):
                # Decide qual tool usar: concorrente específico ou mercado genérico
                use_market_web = not _has_specific_competitor(query_clean)
                tool_label = 'tool.market_research' if use_market_web else 'tool.competitive_research'

                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'tool_progress', 'tool': tool_label, 'status': 'start'})}\n\n"

                if use_market_web:
                    response_text = await _run_market_research_fast_path(q)
                else:
                    response_text = await _run_competitive_market_fast_path(q)
                response_text = _sanitize_business_output(response_text)

                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'tool_progress', 'tool': 'system.finalizing', 'status': 'finishing'})}\n\n"

                words = response_text.split(" ")
                for i in range(0, len(words), 10):
                    chunk_words = words[i:i + 10]
                    prefix = " " if i > 0 else ""
                    chunk_text = prefix + " ".join(chunk_words)
                    event_counter += 1
                    yield f"id: {event_counter}\n"
                    yield f"data: {safe_json_dumps({'type': 'text', 'text': chunk_text, 'done': False})}\n\n"

                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'final', 'text': '', 'done': True})}\n\n"
                final_sent = True
                return

            # --- FAST PATH: perguntas determinísticas de KPI (sem LLM) ---
            kpi_intents = [
                "kpi",
                "kpis",
                "indicadores",
                "metricas",
                "métricas",
                "resumo executivo",
            ]
            if any(term in query_clean for term in kpi_intents) and len(query_clean) <= 60:
                deterministic_msg = (
                    "Para KPIs instantâneos, use o Dashboard/endpoint de métricas. "
                    "Posso detalhar um KPI específico se você informar qual (ex.: venda_30dd, margem, estoque)."
                )
                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'text', 'text': deterministic_msg, 'done': False})}\n\n"
                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'final', 'text': '', 'done': True})}\n\n"
                final_sent = True
                return
            # ---------------------------------------------------------------------

            # [DEBUG] FIX: Ensure initialization if startup task hasn't finished yet
            if chat_service_v3 is None:
                logger.info("[RETRY] Agent system not ready yet. Waiting for initialization...")
                await initialize_agents_async()

            if chat_service_v3 is None:
                yield f"data: {safe_json_dumps({'error': 'Agent system could not be initialized'})}\n\n"
                return

            # Retrieve History - Corrected with user_id for security
            # chat_history = session_manager.get_history(session_id, current_user.id)
            # Add User Message to History immediately
            # session_manager.add_message(session_id, "user", q, current_user.id)

            logger.info(f"Processing query with ChatServiceV3: '{q}'")

            # [OK] FIX 2026-01-14: Cache agora usa user_id para isolamento
            # Isso evita que dados de UNE 1685 sejam retornados para query de UNE 1700
            user_cache_id = str(current_user.id) if current_user else None
            metrics = MetricsService()

            # NOVO: Verificar Semantic Cache primeiro (com user_id)
            cache_key_query = f"{_CHAT_CACHE_VERSION}:{q}"
            metrics.increment("chat_cache_lookups_total")
            cached_response = cache_get(cache_key_query, user_id=user_cache_id)
            if cached_response and not _is_degraded_or_error_response(cached_response):
                metrics.increment("chat_cache_hits_total")
                logger.info(f"CACHE HIT: Resposta encontrada em cache para: {q[:50]}... (user={user_cache_id})")
                # Mesmo em cache-hit, manter histórico consistente para follow-ups.
                try:
                    if chat_service_v3 is not None:
                        chat_service_v3.session_manager.add_message(session_id, "user", q, current_user.id)
                        cached_text = ""
                        if isinstance(cached_response, dict):
                            res = cached_response.get("result", {})
                            if isinstance(res, dict):
                                cached_text = str(res.get("mensagem", ""))
                            else:
                                cached_text = str(res)
                        if not cached_text:
                            cached_text = str(cached_response)
                        chat_service_v3.session_manager.add_message(session_id, "assistant", cached_text, current_user.id)
                except Exception as e:
                    logger.warning(f"Falha ao registrar histórico em cache-hit: {e}")
                event_counter += 1
                yield f"id: {event_counter}\n"
                yield f"data: {safe_json_dumps({'type': 'cache_hit', 'done': False})}\n\n"
                agent_response = cached_response
            elif cached_response:
                metrics.increment("chat_cache_misses_total")
                logger.info("CACHE SKIP: resposta degradada/erro não será reutilizada")
                agent_response = None
            else:
                metrics.increment("chat_cache_misses_total")
                # OPTIMIZATION 2025: Stream progress events during agent execution
                import asyncio
                event_queue = asyncio.Queue()

                async def progress_callback(event):
                    await event_queue.put(event)

                # [OK] FIX: Timeout reduzido de 300s para 60s (resposta mais rápida)
                agent_task = asyncio.create_task(
                    asyncio.wait_for(
                        chat_service_v3.process_message(
                            query=q, 
                            session_id=session_id, 
                            user_id=current_user.id,
                            user_role=current_user.role,
                            on_progress=progress_callback
                        ),
                        timeout=90.0  # [OK] FIX: Aumentado para 90s para queries complexas com gráficos
                    )
                )

                # Stream progress events as they arrive
                agent_response = None
                keepalive_counter = 0
                keepalive_interval = 50  # Send keepalive every 5s (50 * 0.1s)

                while True:
                    try:
                        event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                        event_counter += 1
                        keepalive_counter = 0  # Reset keepalive on real event
                        yield f"id: {event_counter}\n"
                        yield f"data: {safe_json_dumps(event)}\n\n"
                    except asyncio.TimeoutError:
                        keepalive_counter += 1

                        # Send keepalive event every 5 seconds to prevent frontend timeout
                        if keepalive_counter >= keepalive_interval:
                            event_counter += 1
                            keepalive_event = {"type": "keepalive", "message": "Ainda processando sua análise complexa..."}
                            yield f"id: {event_counter}\n"
                            yield f"data: {safe_json_dumps(keepalive_event)}\n\n"
                            keepalive_counter = 0

                        if agent_task.done():
                            try:
                                agent_response = agent_task.result()
                            except asyncio.TimeoutError:
                                logger.error(f"Agent timeout após 90s para query: {q}")
                                if _is_competitive_market_query(q):
                                    recovered_text = await _run_competitive_market_fast_path(q)
                                    agent_response = {
                                        "type": "text",
                                        "result": {"mensagem": recovered_text}
                                    }
                                else:
                                    agent_response = {
                                        "type": "text",
                                        "result": {
                                            "mensagem": "O tempo limite de processamento foi excedido (90 segundos). Tente uma pergunta mais objetiva para receber a resposta mais rápido."
                                        }
                                    }
                            except Exception as e:
                                logger.error(f"Agent error: {e}", exc_info=True)
                                agent_response = {
                                    "type": "text",
                                    "result": {
                                        "mensagem": "Nao foi possivel concluir a analise agora. Tente novamente em instantes."
                                    }
                                }
                            break

                # [OK] FIX 2026-01-14: Salvar resposta válida em cache COM user_id
                if agent_response and "error" not in str(agent_response).lower() and not _is_degraded_or_error_response(agent_response):
                    cache_set(cache_key_query, agent_response, user_id=user_cache_id)
            
            if not agent_response:
                logger.warning(f"Agent retornou resposta vazia para query: {q}")
                agent_response = {
                    "type": "text",
                    "result": {
                        "mensagem": "Não foi possível concluir a análise agora. Verifique limites de quota/billing e tente uma pergunta mais objetiva."
                    }
                }
            
            # Logging detalhado da resposta do agente (nível informativo)
            logger.info(f"[DEBUG] DEBUG - AGENT RESPONSE TYPE: {type(agent_response)}")
            logger.info(f"[DEBUG] DEBUG - AGENT RESPONSE KEYS: {agent_response.keys() if isinstance(agent_response, dict) else 'NOT A DICT'}")
            logger.info(f"[DEBUG] DEBUG - AGENT RESPONSE RAW: {str(agent_response)[:1000]}")
            
            logger.info(f"Agent response received: {agent_response}")

            # Validação de qualidade da resposta (guardrail enterprise)
            validation = validate_response(agent_response, q)
            
            response_type = agent_response.get("type", "text")
            response_content = agent_response.get("result")
            response_text = ""

            if response_type == "text" or response_type == "tool_result":
                # CRITICAL FIX: Check if tool_result contains chart_data from chart generation tools
                result_data = agent_response.get("result", {})
                
                # [OK] FIX 2026-01-17: Check top-level chart_data FIRST (ChatServiceV3 format)
                chart_data = agent_response.get("chart_data")
                
                # Fallback: Check inside result dict (legacy format)
                if not chart_data and isinstance(result_data, dict):
                    chart_data = result_data.get("chart_data") or result_data.get("chart_spec")
                
                # [OK] STREAM CHART IF FOUND (either top-level or legacy)
                if chart_data:
                    logger.info("Chart data detected - streaming chart to frontend")
                    # Parse chart_data if it's a JSON string
                    import json
                    if isinstance(chart_data, str):
                        try:
                            chart_data = json.loads(chart_data)
                        except json.JSONDecodeError:
                            logger.error("Failed to parse chart_data JSON string")
                            chart_data = None
                    
                    if chart_data:
                        # Stream the chart
                        event_counter += 1
                        yield f"id: {event_counter}\n"
                        yield f"data: {safe_json_dumps({'type': 'chart', 'chart_spec': chart_data, 'done': False})}\n\n"
                        
                        # Set response text from result's mensagem if available
                        if isinstance(result_data, dict):
                            response_text = result_data.get("mensagem", "Gráfico gerado com sucesso.")
                        else:
                            response_text = "Gráfico gerado com sucesso."
                
                # Only try to get mensagem if no chart was found
                if not chart_data:
                    if isinstance(result_data, dict):
                         response_text = result_data.get("mensagem", "")
                         evidence = result_data.get("evidencia")
                         if evidence:
                             response_text = f"{response_text}\n\nEvidência: {evidence}"
                    else:
                         response_text = str(result_data)
                    
                    if not response_text or (isinstance(response_text, str) and not response_text.strip()):
                        response_text = "Resposta processada." # Fallback

                if not isinstance(response_text, str):
                    response_text = str(response_text)
            
            
            elif response_type == "code_result":
                # Lógica V2: O LangGraph abstrai "code_result" para "tool_result" ou texto direto
                # Mas mantemos compatibilidade caso o output seja complexo
                chart_spec = agent_response.get("chart_spec")
                response_text = agent_response.get("text_override") or str(response_content)

                if chart_spec:
                    event_counter += 1
                    yield f"id: {event_counter}\n"
                    yield f"data: {safe_json_dumps({'type': 'chart', 'chart_spec': chart_spec, 'done': False})}\n\n"
            
            # Reforço de qualidade interno: não expor detalhes técnicos ao usuário final.
            if response_text and response_text.strip() and not validation.is_valid:
                logger.warning(
                    f"[QUALITY] Resposta com baixa confiança para query='{q[:120]}': "
                    f"issues={validation.issues[:3]} suggestions={validation.suggestions[:2]}"
                )

            if response_text and response_text.strip():
                sanitized = _sanitize_business_output(response_text)
                if sanitized != response_text:
                    logger.info("[QUALITY] Sanitizacao de saida aplicada para remover termos tecnicos.")
                response_text = sanitized

            # Só fazer streaming de texto se houver texto para enviar
            if response_text and response_text.strip():
                words = response_text.split(" ")
                # [OK] FIX: Otimizado de 1 para 8 palavras por chunk (8x mais rápido)
                chunk_size = 8 
                
                logger.info(f"Initiating text streaming of {len(words)} words...")
                
                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i + chunk_size]
                    # Reconstruct spacing correctly
                    prefix = " " if i > 0 else ""
                    chunk_text = prefix + " ".join(chunk_words)
                    
                    event_counter += 1

                    yield f"id: {event_counter}\n"
                    yield f"data: {safe_json_dumps({'type': 'text', 'text': chunk_text, 'done': False})}\n\n"
                    
                    # Small delay to simulate typing speed if needed, but usually network latency is enough
                    # await asyncio.sleep(0.01)

            logger.info("Text streaming complete. Sending done signal.")

        except APIError as e:
            logger.error(f"Agent API Error in stream: {e.message}", exc_info=True)
            yield f"data: {safe_json_dumps({'type': 'error', 'error': e.message, 'details': e.details})}\n\n"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error in stream: {error_msg}", exc_info=True)

            # Generic user-friendly error (never expose technical details)
            error_response = {
                'type': 'error',
                'error': 'Não foi possível processar sua solicitação no momento. Por favor, tente novamente.',
                'error_type': 'generic'
            }

            yield f"data: {safe_json_dumps(error_response)}\n\n"
        finally:
            # 🛑 SAFETY NET: Always send DONE signal to prevent frontend infinite spinner
            if not final_sent:
                yield f"data: {safe_json_dumps({'type': 'final', 'text': '', 'done': True})}\n\n"

    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/feedback")
async def submit_feedback(
    feedback_data: FeedbackRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": current_user.username,
        "response_id": feedback_data.response_id,
        "feedback_type": feedback_data.feedback_type,
        "comment": feedback_data.comment
    }
    
    feedback_file_path = Path(settings.LEARNING_FEEDBACK_PATH) / "feedback.jsonl"
    os.makedirs(Path(settings.LEARNING_FEEDBACK_PATH), exist_ok=True)
    try:
        with open(feedback_file_path, "a", encoding="utf-8") as f:
            f.write(safe_json_dumps(feedback_entry, ensure_ascii=False) + "\n")
        logger.info(f"Feedback submitted by {current_user.username}: {feedback_entry}")
    except OSError as e:
        logger.error(f"Failed to write feedback to file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nao foi possivel salvar o feedback agora."
        )

    return {"message": "Feedback submitted successfully."}

@router.post("", response_class=ORJSONResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    # Legacy - calling agent without history for now, or could pass session_id if we updated request model
    logger.warning("Legacy chat endpoint used.")

    # [DEBUG] FIX: Ensure initialization
    if chat_service_v3 is None:
        logger.info("[RETRY] Lazy initializing agents on first request...")
        await initialize_agents_async()
    
    # We still use the global old variable if needed or refactor completely.
    # Ideally, we should use chat_service_v3, but the legacy code expects 'caculinha_bi_agent'.
    # For now, let's assume ChatServiceV3 initializes the agent internally and we can access it
    # OR we just fail gracefully since this endpoint is legacy.
    
    # Hack: Attempt to get the agent from the service if possible, or re-init (bad).
    # Given this is legacy and likely unused by the new frontend, we just try to init.
    
    # Note: caculinha_bi_agent is imported but not managed by initialize_agents_async directly in this scope
    # unless we expose it. But for the demo, let's focus on the streaming endpoint.
    
    if chat_service_v3 is None:
         raise HTTPException(status_code=500, detail="Servico de chat ainda nao inicializado.")

    # Assuming no history for legacy non-session calls
    # We will use the NEW service instead of the old agent directly to ensure consistency
    result = await chat_service_v3.process_message(
        query=request.query,
        session_id="legacy",
        user_id=current_user.id,
        user_role=current_user.role
    )
    return {"response": str(result), "full_agent_response": result}


@router.get("/history")
async def get_chat_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Legacy contract endpoint for frontend/tests compatibility.
    """
    return {"items": [], "user": current_user.username}
