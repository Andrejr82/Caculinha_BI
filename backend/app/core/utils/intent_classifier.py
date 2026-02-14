"""
Intent Classifier - Sistema Universal de Classificação de Intenções
Classifica queries do usuário em 8 categorias de intenção para seleção correta de ferramentas.

Author: Backend Specialist Agent
Date: 2026-01-24
"""

import re
import logging
from enum import Enum
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Tipos de intenção do usuário."""
    VISUALIZATION = "visualization"      # Gráficos, rankings, dashboards
    DATA_QUERY = "data_query"           # Consultas simples de dados
    ANALYSIS = "analysis"               # Análises descritivas/diagnósticas
    FORECASTING = "forecasting"         # Previsões e tendências
    CALCULATION = "calculation"         # Cálculos (EOQ, MC, preço)
    ANOMALY_DETECTION = "anomaly"       # Detecção de anomalias
    OPTIMIZATION = "optimization"       # Otimizações (transferências, alocação)
    METADATA = "metadata"               # Informações sobre schema


@dataclass
class IntentClassification:
    """Resultado da classificação de intenção."""
    intent: IntentType
    confidence: float  # 0.0 - 1.0
    matched_patterns: List[str]
    query: str


# Padrões de detecção para cada tipo de intenção
# Ordenados por prioridade (mais específicos primeiro)
INTENT_PATTERNS = {
    IntentType.VISUALIZATION: [
        # Padrões explícitos de gráfico
        (r"gere?\s+(um\s+|o\s+)?gr[aá]fico", 0.95),
        (r"mostre\s+(um\s+|o\s+)?gr[aá]fico", 0.95),
        (r"crie?\s+(um\s+|o\s+)?gr[aá]fico", 0.95),
        (r"fa[çc]a\s+(um\s+|o\s+)?gr[aá]fico", 0.95),
        
        # Padrões de ranking e comparação
        (r"ranking\s+de", 0.92),
        (r"top\s+\d+", 0.90),
        (r"maiores\s+\w+", 0.85),
        (r"menores\s+\w+", 0.85),
        (r"compare?", 0.88),
        (r"compara[çc][aã]o\s+(de|entre)", 0.88),
        
        # Padrões de visualização
        (r"visuali[zs]e?", 0.87),
        (r"visualiza[çc][aã]o", 0.87),
        (r"dashboard", 0.90),
        (r"plote", 0.85),
        (r"mostre\s+graficamente", 0.92),
    ],
    
    IntentType.FORECASTING: [
        # Padrões de previsão
        (r"previs[aã]o\s+de", 0.95),
        (r"forecast", 0.93),
        (r"tend[eê]ncia\s+de", 0.88),
        (r"vai\s+vender", 0.90),
        (r"ir[aá]\s+vender", 0.90),
        (r"pr[oó]ximos?\s+\d+\s+(dias|meses|semanas)", 0.92),
        (r"futuro", 0.75),
        (r"estimar\s+vendas", 0.88),
        (r"proje[çc][aã]o", 0.87),
    ],
    
    IntentType.CALCULATION: [
        # Padrões de cálculo
        (r"calcule?\s+(o\s+|a\s+)?eoq", 0.98),
        (r"qual\s+(o\s+|a\s+)?eoq", 0.95),  # Novo padrão
        (r"lote\s+econ[oô]mico", 0.95),
        (r"quanto\s+comprar", 0.90),
        (r"quantidade\s+(ideal|[oó]tima)\s+de\s+compra", 0.92),
        (r"margem\s+de\s+contribui[çc][aã]o", 0.95),
        (r"\bmc\s+do\s+produto", 0.93),
        (r"qual\s+(a\s+)?margem", 0.90),  # Novo padrão
        (r"qual\s+(o\s+)?pre[çc]o\s+final", 0.90),  # Novo padrão
        (r"pre[çc]o\s+final", 0.88),
        (r"calcule?\s+(o\s+|a\s+)?pre[çc]o", 0.85),
        (r"calcule?\s+(o\s+|a\s+)?margem", 0.88),
    ],
    
    IntentType.ANOMALY_DETECTION: [
        # Padrões de anomalia
        (r"detecte?\s+anomalias?", 0.98),
        (r"vendas?\s+anormais?", 0.95),
        (r"outliers?", 0.93),
        (r"picos?\s+de\s+venda", 0.90),
        (r"quedas?\s+bruscas?", 0.90),
        (r"comportamento\s+anormal", 0.92),
        (r"padr[aã]o\s+estranho", 0.88),
        (r"identifique?\s+outliers?", 0.95),
    ],
    
    IntentType.OPTIMIZATION: [
        # Padrões de otimização
        (r"distribui[rz]\s+estoque", 0.95),
        (r"aloc(ar|a[çc][aã]o)\s+de\s+estoque", 0.95),
        (r"transfer[eê]ncia\s+entre\s+lojas", 0.92),
        (r"suger(ir|a)\s+transfer[eê]ncias?", 0.93),
        (r"otimi[zs](ar|a[çc][aã]o)", 0.88),
        (r"melhor\s+distribui[çc][aã]o", 0.90),
        (r"como\s+distribuir", 0.87),
        (r"suger(e|ir|est[aã]o)", 0.85),
    ],
    
    IntentType.ANALYSIS: [
        # Padrões de negócio comercial (alta prioridade prática)
        (r"ruptur\w*", 0.92),
        (r"falta\s+de\s+estoque", 0.90),
        (r"vend\w*\s+negativ\w*", 0.90),
        (r"vend\w*\s+ruin\w*", 0.88),
        (r"piores?\s+grupos?", 0.86),

        # Padrões de análise (mais genéricos, menor prioridade)
        (r"analis(e|ar)\s+\w+", 0.80),
        (r"an[aá]lise\s+(de|do|da)", 0.80),
        (r"como\s+(est[aá]|vai)\s+o", 0.75),
        (r"situa[çc][aã]o\s+d[eo]", 0.78),
        (r"diagn[oó]stico", 0.82),
        (r"avalia[çc][aã]o\s+de", 0.80),
        (r"relat[oó]rio\s+(de|sobre)", 0.83),
        (r"panorama", 0.78),
        (r"vis[aã]o\s+geral", 0.77),
        (r"promoc?i?o?nal", 0.85),
        (r"promo[çc][aã]o", 0.85),
        (r"campanha", 0.82),
        (r"estrategia", 0.80),
        (r"ajud[ae]", 0.80),
        (r"problema", 0.78),
        (r"conselho", 0.80),
        (r"opini[aã]o", 0.78),
        (r"o\s+que\s+fa[çc]o", 0.85),
    ],
    
    IntentType.DATA_QUERY: [
        # Padrões de consulta simples
        (r"^quanto\s+", 0.85),
        (r"^qual\s+(o|a|os|as)", 0.83),
        (r"^quais\s+", 0.83),
        (r"^mostre\s+", 0.80),
        (r"^liste\s+", 0.85),
        (r"^exiba\s+", 0.82),
        (r"dados\s+d[eo]", 0.75),
        (r"informa[çc][oõ]es\s+sobre", 0.78),
    ],
    
    IntentType.METADATA: [
        # Padrões de metadados
        (r"quais\s+colunas", 0.98),
        (r"que\s+dados\s+tenho", 0.95),
        (r"schema", 0.97),
        (r"estrutura\s+d(o|a)\s+(banco|tabela)", 0.95),
        (r"dicion[aá]rio\s+de\s+dados", 0.98),
        (r"metadados", 0.96),
        (r"campos\s+dispon[ií]veis", 0.93),
    ],
}


def classify_intent(query: str) -> IntentClassification:
    """
    Classifica a intenção do usuário baseado em padrões regex.
    
    Args:
        query: Query do usuário em linguagem natural
        
    Returns:
        IntentClassification com intent, confidence e matched patterns
    """
    query_lower = query.lower().strip()
    
    # Acumulador de scores por intent
    intent_scores = {intent: 0.0 for intent in IntentType}
    matched_patterns_by_intent = {intent: [] for intent in IntentType}
    
    # Testar todos os padrões
    for intent_type, patterns in INTENT_PATTERNS.items():
        for pattern, base_confidence in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                # Score = base_confidence × (1 + bonus por match no início)
                position_bonus = 0.1 if match.start() < 10 else 0.0
                score = base_confidence + position_bonus
                
                # Acumular score (múltiplos matches aumentam confiança)
                # O primeiro match vale 100%, os seguintes valem 50% (bônus cumulativo)
                if intent_scores[intent_type] == 0.0:
                     intent_scores[intent_type] = score
                else:
                     intent_scores[intent_type] += score * 0.5
                matched_patterns_by_intent[intent_type].append(pattern)
                
                logger.debug(f"[INTENT] Matched pattern '{pattern}' for {intent_type.value} (score: {score:.2f})")
    
    # Normalizar scores (cap em 1.0)
    for intent in intent_scores:
        intent_scores[intent] = min(intent_scores[intent], 1.0)
    
    # Selecionar intent com maior score
    best_intent = max(intent_scores, key=intent_scores.get)
    best_confidence = intent_scores[best_intent]
    
    # Fallback: Se nenhum padrão matched (confidence = 0), usar DATA_QUERY como default
    if best_confidence == 0.0:
        logger.warning(f"[INTENT] No patterns matched for query: '{query}'. Defaulting to DATA_QUERY.")
        best_intent = IntentType.DATA_QUERY
        best_confidence = 0.50  # Baixa confiança
        matched_patterns_by_intent[best_intent] = ["<fallback>"]
    
    result = IntentClassification(
        intent=best_intent,
        confidence=best_confidence,
        matched_patterns=matched_patterns_by_intent[best_intent],
        query=query
    )
    
    logger.info(
        f"[INTENT] Classified as {result.intent.value} "
        f"(confidence: {result.confidence:.2f}, "
        f"patterns: {len(result.matched_patterns)})"
    )
    
    return result


def get_intent_description(intent: IntentType) -> str:
    """Retorna descrição legível do tipo de intenção."""
    descriptions = {
        IntentType.VISUALIZATION: "Visualização de dados (gráficos, rankings, dashboards)",
        IntentType.DATA_QUERY: "Consulta simples de dados",
        IntentType.ANALYSIS: "Análise descritiva ou diagnóstica",
        IntentType.FORECASTING: "Previsão de vendas ou tendências",
        IntentType.CALCULATION: "Cálculos (EOQ, margem, preço)",
        IntentType.ANOMALY_DETECTION: "Detecção de anomalias ou outliers",
        IntentType.OPTIMIZATION: "Otimização (transferências, alocação)",
        IntentType.METADATA: "Informações sobre schema/metadados",
    }
    return descriptions.get(intent, "Desconhecido")
