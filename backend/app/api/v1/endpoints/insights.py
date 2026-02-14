"""
AI Insights Endpoints - Ultra-Fast Mode with Daily Cache
Retorna insights com cache de 24h para economizar tokens LLM
"""
from typing import Any, List
from datetime import datetime, timedelta
import logging
import json
import hashlib
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.api.dependencies import get_current_user
from backend.app.infrastructure.database.models import User

router = APIRouter(prefix="/insights", tags=["AI Insights"])
logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = Path("data/cache/insights")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_HOURS = 24  # Cache insights for 24 hours

class InsightResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    severity: str
    recommendation: str | None
    created_at: str

class InsightsListResponse(BaseModel):
    insights: List[InsightResponse]
    total: int
    generated_at: str
    cached: bool = False
    cache_age_hours: float = 0.0


def _is_degraded_insight_item(item: dict) -> bool:
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    markers = [
        "sistema de insights em manutenção",
        "falha após",
        "resource_exhausted",
        "quota",
        "you exceeded your current quota",
    ]
    return any(m in text for m in markers)


def _is_degraded_cached_payload(cached: dict) -> bool:
    insights = cached.get("insights", []) if isinstance(cached, dict) else []
    return any(_is_degraded_insight_item(item) for item in insights if isinstance(item, dict))


def _get_cache_key(filters: dict) -> str:
    """Generate cache key based on filters"""
    filter_str = json.dumps(filters or {}, sort_keys=True)
    return hashlib.md5(filter_str.encode()).hexdigest()


def _get_cached_insights(cache_key: str) -> dict | None:
    """Load cached insights if fresh (< 24h)"""
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)

        # Check if cache is still fresh
        cached_at = datetime.fromisoformat(cached_data.get('generated_at', '2020-01-01'))
        age = datetime.utcnow() - cached_at

        if age.total_seconds() / 3600 < CACHE_TTL_HOURS:
            logger.info(f"[OK] Cache HIT for key {cache_key} (age: {age.total_seconds()/3600:.1f}h)")
            return {
                'insights': cached_data.get('insights', []),
                'cached': True,
                'cache_age_hours': age.total_seconds() / 3600
            }
        else:
            logger.info(f"[TIME] Cache EXPIRED for key {cache_key} (age: {age.total_seconds()/3600:.1f}h)")
            return None

    except Exception as e:
        logger.warning(f"Error reading cache: {e}")
        return None


def _save_insights_to_cache(cache_key: str, insights: List[dict]):
    """Save insights to cache"""
    cache_file = CACHE_DIR / f"{cache_key}.json"

    try:
        cache_data = {
            'insights': insights,
            'generated_at': datetime.utcnow().isoformat(),
            'cache_key': cache_key
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Insights cached to {cache_file}")

    except Exception as e:
        logger.error(f"Error saving cache: {e}")

@router.get("/proactive", response_model=InsightsListResponse)
async def get_proactive_insights(current_user: User = Depends(get_current_user)) -> Any:
    """
    🧠 MODO ANALÍTICO REAL com Cache de 24h: Retorna insights usando Gemini/Groq
    Cache economiza tokens LLM - nova geração apenas 1x por dia por perfil
    """
    try:
        from backend.app.config.settings import settings
        import uuid

        # Filtros baseados no perfil do usuario
        filters = {}
        if current_user.segments_list:
            filters["segments"] = current_user.segments_list

        # Generate cache key
        cache_key = _get_cache_key(filters)

        # Try cache first
        cached = _get_cached_insights(cache_key)
        if cached and not _is_degraded_cached_payload(cached):
            insights = []
            for i, item in enumerate(cached['insights']):
                insights.append(InsightResponse(
                    id=f"ins-{uuid.uuid4().hex[:8]}",
                    title=item.get("title", "Insight"),
                    description=item.get("description", ""),
                    category=item.get("category", "info"),
                    severity=item.get("severity", "low"),
                    recommendation=item.get("recommendation"),
                    created_at=datetime.utcnow().isoformat()
                ))

            logger.info(f"[OK] Returning cached insights (age: {cached['cache_age_hours']:.1f}h)")
            return InsightsListResponse(
                insights=insights,
                total=len(insights),
                generated_at=datetime.utcnow().isoformat(),
                cached=True,
                cache_age_hours=cached['cache_age_hours']
            )
        elif cached:
            logger.info("[CACHE] Degraded insights cache detected. Forcing fresh regeneration.")

        # Cache miss - generate new insights
        logger.info(f"[RETRY] Cache MISS - Generating new insights via LLM (will consume tokens)")

        raw_insights = []

        # ------------------------------------------------------------------
        # MODO OFFLINE (Mock / LangGraph Local)
        # ------------------------------------------------------------------
        if settings.LLM_PROVIDER == "mock" or settings.DEV_FAST_MODE:
            logger.info("⚡ [INSIGHTS] Gerando insights via Heurística (Offline Mode)")
            raw_insights = await _generate_offline_insights()

        # ------------------------------------------------------------------
        # MODO LLM (Gemini / Groq) e Fallback
        # ------------------------------------------------------------------
        else:
            from backend.app.services.llm_insights import LLMInsightsService

            logger.info(f"[SEARCH] Filtrando insights para segmentos: {filters.get('segments', 'all')}")
            raw_insights = await LLMInsightsService.generate_proactive_insights(filters=filters)

        # Save to cache
        _save_insights_to_cache(cache_key, raw_insights)

        # Mapeia para modelo Pydantic
        insights = []
        for i, item in enumerate(raw_insights):
            insights.append(InsightResponse(
                id=f"ins-{uuid.uuid4().hex[:8]}",
                title=item.get("title", "Insight"),
                description=item.get("description", ""),
                category=item.get("category", "info"),
                severity=item.get("severity", "low"),
                recommendation=item.get("recommendation"),
                created_at=datetime.utcnow().isoformat()
            ))

        logger.info(f"[OK] Insights gerados para '{current_user.username}': {len(insights)} itens (FRESH - tokens consumidos)")
        return InsightsListResponse(
            insights=insights,
            total=len(insights),
            generated_at=datetime.utcnow().isoformat(),
            cached=False,
            cache_age_hours=0.0
        )

    except Exception as e:
        logger.error(f"Erro ao gerar insights: {e}", exc_info=True)
        # Fallback mínimo
        return InsightsListResponse(
            insights=[
                InsightResponse(
                    id="fallback-1",
                    title="Modo Segurança",
                    description="Não foi possível gerar insights detalhados no momento.",
                    category="issue",
                    severity="low",
                    recommendation="Verifique os logs do sistema.",
                    created_at=datetime.utcnow().isoformat()
                )
            ],
            total=1,
            generated_at=datetime.utcnow().isoformat()
        )


async def _generate_offline_insights() -> List[dict]:
    """
    Gera insights determinísticos usando DuckDB diretamente.
    Substitui o LLM no modo offline.
    """
    from backend.app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
    import pandas as pd
    
    insights = []
    
    try:
        adapter = get_duckdb_adapter()
        # 1. Insight de Vendas/Valor
        # Análise 1: Top Produtos por Valor (Mais seguro que Grupo)
        df_top = adapter.load_data(
            columns=["NOME", "LIQUIDO_38"],
            order_by="LIQUIDO_38 DESC",
            limit=1
        )
        
        if not df_top.empty:
            item = df_top.iloc[0]
            val = item.get('LIQUIDO_38', 0)
            insights.append({
                "title": "Produto de Maior Impacto",
                "description": f"O produto '{item['NOME']}' tem valor unitário de R$ {float(val):,.2f}.",
                "category": "finance",
                "severity": "medium",
                "recommendation": "Verificar disponibilidade em todas as lojas."
            })

        # Análise 2: Quantidade de Produtos (Count)
        # Mais seguro que soma de estoque se o tipo for incerto
        df_count = adapter.execute_aggregation(
             agg_col="PRODUTO",
             agg_func="count",
             group_by=[], 
             limit=1
        )
        if not df_count.empty:
            qtde = df_count.iloc[0].get('valor', df_count.iloc[0, 0])
            insights.append({
                "title": "Total de Produtos",
                "description": f"A base conta com {int(qtde)} produtos cadastrados.",
                "category": "inventory",
                "severity": "info",
                "recommendation": None
            })

        # Análise 3: Produtos de Alto Valor
        df_par = adapter.load_data(
            columns=["PRODUTO", "NOME", "LIQUIDO_38"],
            order_by="LIQUIDO_38 DESC",
            limit=1
        )
        if not df_par.empty:
            item = df_par.iloc[0]
            insights.append({
                "title": "Item Mais Valioso",
                "description": f"'{item['NOME']}' (R$ {item['LIQUIDO_38']}).",
                "category": "product",
                "severity": "low",
                "recommendation": "Destaque este item na vitrine."
            })
            
    except Exception as e:
        logger.error(f"Erro na geração de insights offline: {e}")
        insights.append({
            "title": "Erro na Análise Local",
            "description": f"Falha ao calcular métricas: {str(e)}",
            "category": "system",
            "severity": "high",
            "recommendation": None
        })
    
    # Se nada gerou (Ex: tabela vazia)
    if not insights:
        insights.append({
            "title": "Sem Dados Suficientes",
            "description": "A base de dados parece vazia ou inacessível no momento.",
            "category": "data",
            "severity": "low",
            "recommendation": "Verifique a carga do arquivo parquet."
        })
        
    return insights

@router.get("/anomalies")
async def detect_anomalies():
    return {"status": "ok", "message": "Anomaly detection em desenvolvimento"}

@router.post("/ask")
async def ask_insight_question(question: str):
    return {"answer": "IA ativa em modo econômico. Use o Chat BI para perguntas detalhadas."}
