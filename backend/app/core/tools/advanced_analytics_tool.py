"""
Advanced Analytics Tool - Ferramentas de Análise Avançada para Gemini 2.5 Pro

Este módulo implementa análises estatísticas e ML avançadas que aproveitam
as capacidades STEM do Gemini 2.5 Pro:
- Análise de regressão (linear, polinomial)
- Detecção de anomalias
- Análise de correlação
- Previsão de séries temporais (ARIMA)
- Clustering e segmentação

Author: Agent BI Team
Date: 2026-01-24
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# LangChain tool decorator
try:
    from langchain_core.tools import tool
except ImportError:
    # Fallback decorator
    def tool(func):
        return func

logger = logging.getLogger(__name__)

# Lazy imports para otimizar cold start
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logger.warning("scipy não disponível. Análises estatísticas limitadas.")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn não disponível. ML features desabilitadas.")


def _extract_query_rows(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []

    for key in ("resultados", "dados", "itens"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return rows

    aggregated = payload.get("resultado_agregado")
    if isinstance(aggregated, dict):
        return [aggregated]

    return []


def _resolve_entity_column(df: pd.DataFrame, preferred: str = "UNE") -> Optional[str]:
    candidates = [preferred, "UNE", "LOJA", "loja", "unidade", "UNIDADE"]
    for column in candidates:
        if column in df.columns:
            return column
    return next((column for column in df.columns if "une" in str(column).lower()), None)


def _resolve_numeric_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def _compute_z_scores(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return np.asarray([], dtype=float)
    std = float(arr.std())
    if std == 0:
        return np.zeros_like(arr, dtype=float)
    return (arr - float(arr.mean())) / std


def _load_product_store_frame(produto_id: str) -> pd.DataFrame:
    from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel

    payload = consultar_dados_flexivel(
        filtros={"PRODUTO": produto_id},
        colunas=["PRODUTO", "NOME", "UNE", "VENDA_30DD", "ESTOQUE_UNE", "NOMESEGMENTO"],
        limite=200,
    )
    rows = _extract_query_rows(payload)
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    for column in ("VENDA_30DD", "ESTOQUE_UNE"):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    return df


def segment_records_by_performance(
    records: List[Dict[str, Any]],
    num_clusters: int = 3,
    entity_key: str = "UNE",
) -> Dict[str, Any]:
    df = pd.DataFrame(records or [])
    if df.empty or len(df) < 2:
        return {"error": "Dados insuficientes para segmentação"}

    entity_col = _resolve_entity_column(df, preferred=entity_key)
    sales_col = _resolve_numeric_column(df, ["VENDA_30DD", "TOTAL_VENDAS", "vendas_30d", "valor"])
    stock_col = _resolve_numeric_column(df, ["ESTOQUE_UNE", "estoque_atual", "estoque"])

    if not entity_col or not sales_col:
        return {"error": "Colunas mínimas para clustering não encontradas"}

    df = df.copy()
    df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce").fillna(0.0)
    if stock_col:
        df[stock_col] = pd.to_numeric(df[stock_col], errors="coerce").fillna(0.0)
    else:
        stock_col = "__estoque_virtual__"
        df[stock_col] = 0.0

    sales_per_day = np.where(df[sales_col].to_numpy(dtype=float) > 0, df[sales_col].to_numpy(dtype=float) / 30.0, 0.0)
    coverage_days = np.where(sales_per_day > 0, df[stock_col].to_numpy(dtype=float) / sales_per_day, 365.0)
    coverage_days = np.clip(coverage_days, 0.0, 365.0)

    features = pd.DataFrame(
        {
            "vendas_30d": df[sales_col].to_numpy(dtype=float),
            "estoque_atual": df[stock_col].to_numpy(dtype=float),
            "cobertura_dias": coverage_days,
        }
    )

    desired_clusters = max(2, min(int(num_clusters or 3), len(features)))
    labels: np.ndarray
    method = "quantile"

    if HAS_SKLEARN and desired_clusters > 1:
        normalized = (features - features.mean()) / features.std(ddof=0).replace(0, 1)
        labels = KMeans(n_clusters=desired_clusters, random_state=42, n_init=10).fit_predict(normalized)
        method = "kmeans"
    else:
        percentile = features["vendas_30d"].rank(method="first", pct=True).to_numpy(dtype=float)
        labels = np.minimum((percentile * desired_clusters).astype(int), desired_clusters - 1)

    df["cluster_id"] = labels.astype(int)
    df["vendas_30d"] = features["vendas_30d"]
    df["estoque_atual"] = features["estoque_atual"]
    df["cobertura_dias"] = features["cobertura_dias"]

    cluster_order = (
        df.groupby("cluster_id")
        .agg(media_vendas_30d=("vendas_30d", "mean"), media_cobertura_dias=("cobertura_dias", "mean"))
        .sort_values(["media_vendas_30d", "media_cobertura_dias"], ascending=[False, False])
        .reset_index()
    )

    semantic_names_by_rank = {
        2: ["alta_performance", "oportunidade"],
        3: ["alta_performance", "equilibrado", "oportunidade"],
        4: ["alta_performance", "equilibrado", "atencao", "oportunidade"],
    }
    ordered_names = semantic_names_by_rank.get(
        len(cluster_order),
        [f"cluster_{idx + 1}" for idx in range(len(cluster_order))],
    )
    cluster_name_map = {
        int(row.cluster_id): ordered_names[idx] if idx < len(ordered_names) else f"cluster_{idx + 1}"
        for idx, row in cluster_order.iterrows()
    }

    df["cluster_nome"] = df["cluster_id"].map(cluster_name_map)
    summary: List[Dict[str, Any]] = []
    for cluster_id, group in df.groupby("cluster_id"):
        ordered_group = group.sort_values("vendas_30d", ascending=False)
        summary.append(
            {
                "cluster_id": int(cluster_id),
                "cluster_nome": cluster_name_map[int(cluster_id)],
                "total_entidades": int(len(group)),
                "media_vendas_30d": round(float(group["vendas_30d"].mean()), 2),
                "media_estoque": round(float(group["estoque_atual"].mean()), 2),
                "media_cobertura_dias": round(float(group["cobertura_dias"].mean()), 2),
                "entidades_referencia": [str(value) for value in ordered_group[entity_col].head(3).tolist()],
            }
        )

    clusters = [
        {
            "entidade": str(row[entity_col]),
            "cluster_id": int(row["cluster_id"]),
            "cluster_nome": str(row["cluster_nome"]),
            "vendas_30d": round(float(row["vendas_30d"]), 2),
            "estoque_atual": round(float(row["estoque_atual"]), 2),
            "cobertura_dias": round(float(row["cobertura_dias"]), 2),
        }
        for _, row in df.sort_values(["cluster_id", "vendas_30d"], ascending=[True, False]).iterrows()
    ]

    return {
        "metodo": method,
        "num_clusters": len(summary),
        "clusters": clusters,
        "resumo_clusters": summary,
    }


def classify_stock_risk(
    records: List[Dict[str, Any]],
    horizonte_dias: int = 30,
    entity_key: str = "UNE",
) -> Dict[str, Any]:
    df = pd.DataFrame(records or [])
    if df.empty:
        return {"error": "Dados insuficientes para classificação"}

    entity_col = _resolve_entity_column(df, preferred=entity_key)
    sales_col = _resolve_numeric_column(df, ["VENDA_30DD", "TOTAL_VENDAS", "vendas_30d", "valor"])
    stock_col = _resolve_numeric_column(df, ["ESTOQUE_UNE", "estoque_atual", "estoque"])

    if not entity_col or not sales_col or not stock_col:
        return {"error": "Colunas mínimas para classificação não encontradas"}

    df = df.copy()
    df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce").fillna(0.0)
    df[stock_col] = pd.to_numeric(df[stock_col], errors="coerce").fillna(0.0)

    def _classify(row: pd.Series) -> Tuple[str, float]:
        sales = float(row[sales_col])
        stock = float(row[stock_col])
        daily_sales = sales / 30.0 if sales > 0 else 0.0
        coverage = stock / daily_sales if daily_sales > 0 else 365.0

        if stock <= 0 and sales > 0:
            return "critico", coverage
        if sales <= 0 and stock > 0:
            return "excesso", coverage
        if coverage < 7:
            return "alto_risco", coverage
        if coverage < 15:
            return "moderado", coverage
        return "saudavel", coverage

    classifications: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    for _, row in df.iterrows():
        risk_class, coverage = _classify(row)
        counts[risk_class] = counts.get(risk_class, 0) + 1
        classifications.append(
            {
                "entidade": str(row[entity_col]),
                "classe_risco": risk_class,
                "vendas_30d": round(float(row[sales_col]), 2),
                "estoque_atual": round(float(row[stock_col]), 2),
                "cobertura_dias": round(float(min(coverage, 365.0)), 2),
                "demanda_horizonte": round(float((float(row[sales_col]) / 30.0) * max(1, horizonte_dias)), 2),
            }
        )

    risk_order = {"critico": 0, "alto_risco": 1, "moderado": 2, "saudavel": 3, "excesso": 4}
    classifications.sort(key=lambda item: (risk_order.get(item["classe_risco"], 9), item["cobertura_dias"]))

    return {
        "horizonte_dias": int(horizonte_dias),
        "classificacoes": classifications,
        "resumo_risco": counts,
    }


@tool
def analise_regressao_vendas(
    produto_id: str,
    periodo_dias: int = 90,
    tipo_regressao: str = "linear"
) -> Dict[str, Any]:
    """
    Análise de tendência de vendas por loja.
    
    USE QUANDO: O usuário perguntar "tendência", "crescimento", "declínio", 
    "padrão de vendas", "regressão", "evolução temporal", "comportamento".
    
    NOTA: Dataset atual é snapshot (sem série temporal).
    Analisa variação de vendas entre lojas para identificar padrões.
    
    Args:
        produto_id: ID do produto
        periodo_dias: Não usado (mantido para compatibilidade)
        tipo_regressao: Não usado (mantido para compatibilidade)
    
    Returns:
        {
            "tendencia": "crescente|decrescente|estavel",
            "media_vendas": 100.0,
            "desvio_padrao": 15.0,
            "lojas_top_5": [...],
            "analise": "Descrição da distribuição"
        }
    """
    try:
        df = _load_product_store_frame(produto_id)
        if df.empty:
            return {"error": f"Produto {produto_id} não encontrado"}
        
        # Verificar se tem coluna de vendas
        venda_col = None
        for col in ['VENDA_30DD', 'VENDA30DD', 'VENDAS']:
            if col in df.columns:
                venda_col = col
                break
        
        if not venda_col:
            return {"error": "Coluna de vendas não encontrada no dataset"}
        
        # Converter para numérico
        df[venda_col] = pd.to_numeric(df[venda_col], errors='coerce')
        df = df.dropna(subset=[venda_col])
        
        if len(df) < 3:
            return {"error": "Dados insuficientes (mínimo 3 lojas)"}
        
        # Análise estatística
        vendas = df[venda_col].values
        media = float(np.mean(vendas))
        desvio = float(np.std(vendas))
        mediana = float(np.median(vendas))
        
        # Tendência baseada em distribuição
        if media > mediana * 1.2:
            tendencia = "concentrada_em_poucas_lojas"
        elif desvio / media < 0.3:
            tendencia = "estavel_entre_lojas"
        else:
            tendencia = "variavel_entre_lojas"
        
        # Top 5 lojas
        entity_col = _resolve_entity_column(df) or "UNE"
        df_sorted = df.nlargest(5, venda_col)
        top_lojas = []
        for _, row in df_sorted.iterrows():
            top_lojas.append({
                "loja": str(row.get(entity_col, 'N/A')),
                "vendas_30d": float(row[venda_col])
            })
        
        return {
            "produto": produto_id,
            "total_lojas": len(df),
            "media_vendas_30d": round(media, 2),
            "mediana_vendas_30d": round(mediana, 2),
            "desvio_padrao": round(desvio, 2),
            "coeficiente_variacao": round(desvio / media, 2) if media > 0 else 0,
            "tendencia": tendencia,
            "top_5_lojas": top_lojas,
            "analise": f"Produto vendido em {len(df)} lojas com média de {round(media, 0)} unidades/30d. {tendencia.replace('_', ' ').title()}.",
            "nota": "Análise baseada em snapshot (últimos 30 dias), não série temporal"
        }
        
    except Exception as e:
        logger.error(f"Erro em analise_regressao_vendas: {e}", exc_info=True)
        return {"error": str(e)}


@tool
def detectar_anomalias_vendas(
    produto_id: str,
    periodo_dias: int = 90,
    sensibilidade: float = 2.5
) -> Dict[str, Any]:
    """
    Detecta lojas com vendas anormalmente altas ou baixas.
    
    USE QUANDO: O usuário perguntar "anomalia", "outlier", "pico", "quedas bruscas", 
    "vendas estranhas", "problemas", "inconsistências", "comportamento atípico".
    
    NOTA: Dataset atual é snapshot (sem série temporal).
    Usa Z-score para identificar lojas outliers.
    
    Args:
        produto_id: ID do produto
        periodo_dias: Não usado (mantido para compatibilidade)
        sensibilidade: Threshold de Z-score (2.5 = moderado, 3.0 = extremo)
    
    Returns:
        {
            "anomalias_detectadas": 3,
            "lojas_pico": [...],
            "lojas_baixa": [...],
            "media_vendas": 100.0
        }
    """
    try:
        df = _load_product_store_frame(produto_id)
        if df.empty or len(df) < 7:
            return {"error": "Dados insuficientes para análise estatística (mínimo 7 lojas)"}
        
        # Encontrar coluna de vendas
        venda_col = None
        for col in ['VENDA_30DD', 'VENDA30DD', 'VENDAS']:
            if col in df.columns:
                venda_col = col
                break
        
        if not venda_col:
            return {"error": "Coluna de vendas não encontrada"}
        
        # Converter para numérico
        df[venda_col] = pd.to_numeric(df[venda_col], errors='coerce')
        df = df.dropna(subset=[venda_col])
        
        # Calcular Z-scores
        vendas = df[venda_col].values
        z_scores = _compute_z_scores(vendas)
        
        # Detectar anomalias
        anomalias_idx = np.where(np.abs(z_scores) > sensibilidade)[0]
        
        lojas_pico = []
        lojas_baixa = []
        
        for idx in anomalias_idx:
            entity_col = _resolve_entity_column(df) or "UNE"
            loja = str(df.iloc[idx].get(entity_col, 'N/A'))
            valor = float(df.iloc[idx][venda_col])
            z = float(z_scores[idx])
            
            anomalia = {
                "loja": loja,
                "vendas_30d": valor,
                "z_score": round(z, 2)
            }
            
            if z > 0:
                lojas_pico.append(anomalia)
            else:
                lojas_baixa.append(anomalia)
        
        return {
            "produto": produto_id,
            "anomalias_detectadas": len(anomalias_idx),
            "lojas_pico_vendas": sorted(lojas_pico, key=lambda x: x['z_score'], reverse=True),
            "lojas_baixa_vendas": sorted(lojas_baixa, key=lambda x: x['z_score']),
            "media_vendas_30d": round(float(np.mean(vendas)), 2),
            "desvio_padrao": round(float(np.std(vendas)), 2),
            "coeficiente_variacao": round(float(np.std(vendas) / np.mean(vendas)), 2),
            "sensibilidade_usada": sensibilidade,
            "total_lojas_analisadas": len(df),
            "nota": "Análise baseada em snapshot (últimos 30 dias), não série temporal"
        }
        
    except Exception as e:
        logger.error(f"Erro em detectar_anomalias_vendas: {e}", exc_info=True)
        return {"error": str(e)}


@tool
def analise_correlacao_produtos(
    produtos_ids: List[str],
    periodo_dias: int = 90
) -> Dict[str, Any]:
    """
    Analisa correlação de vendas entre produtos.
    
    USE QUANDO: O usuário perguntar "correlação", "relação", "vendem juntos", 
    "produtos associados", "mix de produtos", "cross-selling", "complementares".
    
    Gemini 2.5 Pro pode usar para identificar produtos complementares ou substitutos.
    
    Args:
        produtos_ids: Lista de IDs de produtos (máx 10)
        periodo_dias: Período de análise
    
    Returns:
        {
            "matriz_correlacao": [[1.0, 0.8], [0.8, 1.0]],
            "pares_alta_correlacao": [
                {"produto_a": "123", "produto_b": "456", "correlacao": 0.85}
            ],
            "interpretacao": "Produtos 123 e 456 são complementares"
        }
    """
    if len(produtos_ids) > 10:
        return {"error": "Máximo 10 produtos para análise de correlação"}
    
    try:
        vendas_por_produto = {}
        for produto_id in produtos_ids:
            df = _load_product_store_frame(produto_id)
            if df.empty:
                continue
            entity_col = _resolve_entity_column(df)
            venda_col = _resolve_numeric_column(df, ['VENDA_30DD', 'VENDA30DD', 'VENDAS'])
            if not entity_col or not venda_col:
                continue
            grouped = df.groupby(entity_col)[venda_col].sum()
            if len(grouped) >= 2:
                vendas_por_produto[produto_id] = grouped
        
        if len(vendas_por_produto) < 2:
            return {"error": "Dados insuficientes para correlação"}
        
        # Criar DataFrame com todas as séries
        df_vendas = pd.DataFrame(vendas_por_produto).fillna(0)
        
        # Calcular matriz de correlação
        corr_matrix = df_vendas.corr()
        
        # Encontrar pares com alta correlação
        pares_alta_corr = []
        for i, prod_a in enumerate(produtos_ids):
            for j, prod_b in enumerate(produtos_ids):
                if i < j:  # Evitar duplicatas
                    corr = corr_matrix.loc[prod_a, prod_b]
                    if abs(corr) > 0.7:  # Alta correlação
                        pares_alta_corr.append({
                            "produto_a": prod_a,
                            "produto_b": prod_b,
                            "correlacao": float(corr),
                            "tipo": "complementares" if corr > 0 else "substitutos"
                        })
        
        return {
            "matriz_correlacao": corr_matrix.values.tolist(),
            "produtos": produtos_ids,
            "pares_alta_correlacao": pares_alta_corr,
            "numero_pares_correlacionados": len(pares_alta_corr)
        }
        
    except Exception as e:
        logger.error(f"Erro em analise_correlacao_produtos: {e}", exc_info=True)
        return {"error": str(e)}


@tool
def segmentar_lojas_por_performance(
    produto_id: str,
    num_clusters: int = 3,
) -> Dict[str, Any]:
    """
    Segmenta as lojas de um produto em grupos de performance.

    USE QUANDO: O usuário perguntar por cluster, segmentação, grupos de lojas,
    perfis de performance ou tierização operacional.
    """
    try:
        df = _load_product_store_frame(produto_id)
        if df.empty:
            return {"error": f"Produto {produto_id} não encontrado"}

        result = segment_records_by_performance(df.to_dict(orient="records"), num_clusters=num_clusters, entity_key="UNE")
        result["produto"] = produto_id
        return result
    except Exception as e:
        logger.error(f"Erro em segmentar_lojas_por_performance: {e}", exc_info=True)
        return {"error": str(e)}


@tool
def classificar_risco_estoque(
    produto_id: str,
    horizonte_dias: int = 30,
) -> Dict[str, Any]:
    """
    Classifica o risco de estoque por loja para um produto.

    USE QUANDO: O usuário pedir classificação de risco, criticidade,
    lojas com maior risco ou priorização de abastecimento.
    """
    try:
        df = _load_product_store_frame(produto_id)
        if df.empty:
            return {"error": f"Produto {produto_id} não encontrado"}

        result = classify_stock_risk(df.to_dict(orient="records"), horizonte_dias=horizonte_dias, entity_key="UNE")
        result["produto"] = produto_id
        return result
    except Exception as e:
        logger.error(f"Erro em classificar_risco_estoque: {e}", exc_info=True)
        return {"error": str(e)}


# Exportar ferramentas
__all__ = [
    'analise_regressao_vendas',
    'detectar_anomalias_vendas',
    'analise_correlacao_produtos',
    'segmentar_lojas_por_performance',
    'classificar_risco_estoque',
    'segment_records_by_performance',
    'classify_stock_risk',
]
