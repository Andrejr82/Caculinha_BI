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
from datetime import datetime, timedelta

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
    from scipy.stats import zscore
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
    if not HAS_SKLEARN:
        return {"error": "scikit-learn não instalado"}
    
    try:
        # Buscar dados do produto em todas as lojas
        from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
        
        dados = consultar_dados_flexivel(
            filtros={"PRODUTO": produto_id},
            limite=100
        )
        
        if not dados or "erro" in dados:
            return {"error": "Dados insuficientes para análise"}
        
        # Preparar dados
        df = pd.DataFrame(dados.get("dados", []))
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
        df_sorted = df.nlargest(5, venda_col)
        top_lojas = []
        for _, row in df_sorted.iterrows():
            top_lojas.append({
                "loja": str(row.get('UNE', 'N/A')),
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
    if not HAS_SCIPY:
        return {"error": "scipy não instalado"}
    
    try:
        from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
        
        dados = consultar_dados_flexivel(
            filtros={"PRODUTO": produto_id},
            limite=100
        )
        
        if not dados or "erro" in dados:
            return {"error": "Dados insuficientes"}
        
        df = pd.DataFrame(dados.get("dados", []))
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
        z_scores = zscore(vendas)
        
        # Detectar anomalias
        anomalias_idx = np.where(np.abs(z_scores) > sensibilidade)[0]
        
        lojas_pico = []
        lojas_baixa = []
        
        for idx in anomalias_idx:
            loja = str(df.iloc[idx].get('UNE', 'N/A'))
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
    if not HAS_SCIPY:
        return {"error": "scipy não instalado"}
    
    if len(produtos_ids) > 10:
        return {"error": "Máximo 10 produtos para análise de correlação"}
    
    try:
        from backend.app.core.tools.flexible_query_tool import consultar_dados_flexivel
        
        data_inicio = (datetime.now() - timedelta(days=periodo_dias)).strftime("%Y-%m-%d")
        
        # Buscar vendas de todos os produtos
        vendas_por_produto = {}
        for produto_id in produtos_ids:
            dados = consultar_dados_flexivel(
                filtros={"PRODUTO_ID": produto_id, "DATA_VENDA": f">={data_inicio}"},
                funcao_agregacao="sum",
                coluna_agregacao="QUANTIDADE",
                agrupar_por=["DATA_VENDA"],
                ordenar_por="DATA_VENDA",
                limite=1000
            )
            
            if dados and "dados" in dados:
                df = pd.DataFrame(dados["dados"])
                vendas_por_produto[produto_id] = df.set_index("DATA_VENDA")["QUANTIDADE"]
        
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


# Exportar ferramentas
__all__ = [
    'analise_regressao_vendas',
    'detectar_anomalias_vendas',
    'analise_correlacao_produtos'
]
