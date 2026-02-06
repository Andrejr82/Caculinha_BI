"""
Seasonality Detector - Detector de Períodos Sazonais

Detecta automaticamente períodos sazonais críticos para o varejo:
- Volta às Aulas (Janeiro-Fevereiro)
- Natal (Novembro-Dezembro)
- Páscoa (Março-Abril)

Usado para ajustar previsões de demanda e recomendações de compra.
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Configuração de períodos sazonais
SEASONAL_PERIODS = {
    "volta_as_aulas": {
        "months": [1, 2],  # Janeiro-Fevereiro
        "coverage_days": 60,  # Estoque recomendado para 60 dias
        "urgency": "ALTA",
        "multiplier": 2.5,  # Demanda aumenta 2.5x
        "description": "Volta às Aulas - Pico de demanda em papelaria e material escolar"
    },
    "natal": {
        "months": [11, 12],  # Novembro-Dezembro
        "coverage_days": 90,
        "urgency": "CRÍTICA",
        "multiplier": 3.0,  # Demanda aumenta 3x
        "description": "Natal - Maior pico do ano em presentes e decoração"
    },
    "pascoa": {
        "months": [3, 4],  # Março-Abril
        "coverage_days": 45,
        "urgency": "MÉDIA",
        "multiplier": 1.8,  # Demanda aumenta 1.8x
        "description": "Páscoa - Pico em chocolates e artigos religiosos"
    },
    "dia_das_maes": {
        "months": [5],  # Maio
        "coverage_days": 30,
        "urgency": "MÉDIA",
        "multiplier": 1.6,
        "description": "Dia das Mães - Pico em presentes e artesanato"
    },
    "dia_dos_pais": {
        "months": [8],  # Agosto
        "coverage_days": 30,
        "urgency": "MÉDIA",
        "multiplier": 1.5,
        "description": "Dia dos Pais - Pico em presentes masculinos"
    }
}

# Mapeamento: Período Sazonal → Segmentos Afetados
# Apenas produtos destes segmentos receberão alertas sazonais
SEASONAL_SEGMENTS = {
    "volta_as_aulas": [
        "PAPELARIA",
        "MATERIAL ESCOLAR",
        "LIVROS",
        "MOCHILAS E BOLSAS",
        "INFORMÁTICA",  # Notebooks, tablets para estudantes
        "ELETRÔNICOS"   # Calculadoras, etc.
    ],
    "natal": [
        "BRINQUEDOS",
        "PRESENTES",
        "DECORAÇÃO",
        "CASA E DECORAÇÃO",
        "ELETRÔNICOS",
        "PERFUMARIA",
        "MODA",
        "JOIAS E BIJUTERIAS",
        "LIVROS"
    ],
    "pascoa": [
        "CHOCOLATES",
        "DOCES",
        "CONFEITARIA",
        "ARTIGOS RELIGIOSOS",
        "DECORAÇÃO"
    ],
    "dia_das_maes": [
        "PRESENTES",
        "PERFUMARIA",
        "JOIAS E BIJUTERIAS",
        "FLORES",
        "ARTESANATO",
        "MODA"
    ],
    "dia_dos_pais": [
        "FERRAMENTAS",
        "ELETRÔNICOS",
        "ESPORTES",
        "BEBIDAS",
        "PRESENTES",
        "MODA"
    ]
}


def detect_seasonal_context(
    reference_date: Optional[datetime] = None,
    produto_segmento: Optional[str] = None
) -> Optional[Dict]:
    """
    Detecta se estamos em período sazonal E se o produto pertence a um segmento afetado.
    
    Args:
        reference_date: Data de referência (se None, usa data atual)
        produto_segmento: Segmento do produto (ex: "PAPELARIA", "CASA E DECORAÇÃO")
    
    Returns:
        {
            "season": Nome do período (ex: "volta_as_aulas"),
            "coverage_days": Dias de estoque recomendados,
            "urgency": Nível de urgência ("BAIXA", "MÉDIA", "ALTA", "CRÍTICA"),
            "multiplier": Multiplicador de demanda,
            "description": Descrição do período,
            "message": Mensagem formatada,
            "current_month": Mês atual,
            "days_until_peak": Dias até o pico (se aplicável),
            "produto_segmento": Segmento do produto (se fornecido)
        }
        
        None se não estiver em período sazonal OU se o segmento não for afetado
    
    Examples:
        >>> detect_seasonal_context(datetime(2026, 1, 15), "PAPELARIA")
        {
            "season": "volta_as_aulas",
            "urgency": "ALTA",
            "multiplier": 2.5,
            "message": "MODO VOLTA ÀS AULAS ATIVADO",
            ...
        }
        
        >>> detect_seasonal_context(datetime(2026, 1, 15), "CASA E DECORAÇÃO")
        None  # CASA E DECORAÇÃO não tem alta em volta às aulas
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    current_month = reference_date.month
    current_day = reference_date.day
    
    # Verificar cada período sazonal
    for season_name, config in SEASONAL_PERIODS.items():
        if current_month in config["months"]:
            # [OK] NOVO: Verificar se o segmento do produto está na lista de afetados
            if produto_segmento:
                affected_segments = SEASONAL_SEGMENTS.get(season_name, [])
                # Normalizar para uppercase para comparação case-insensitive
                produto_segmento_upper = produto_segmento.upper().strip()
                affected_segments_upper = [s.upper().strip() for s in affected_segments]
                
                if produto_segmento_upper not in affected_segments_upper:
                    logger.debug(
                        f"[SEARCH] Produto do segmento '{produto_segmento}' não é afetado por '{season_name}'. "
                        f"Segmentos afetados: {affected_segments}. Pulando sazonalidade."
                    )
                    continue  # Pular este período sazonal
            
            # Calcular dias até o pico (meio do período)
            peak_month = config["months"][len(config["months"]) // 2]
            peak_day = 15  # Meio do mês
            
            if current_month < peak_month:
                days_until_peak = (peak_month - current_month) * 30 + (peak_day - current_day)
            elif current_month == peak_month:
                days_until_peak = peak_day - current_day
            else:
                days_until_peak = -(current_day - peak_day)  # Negativo = já passou
            
            context = {
                "season": season_name,
                "coverage_days": config["coverage_days"],
                "urgency": config["urgency"],
                "multiplier": config["multiplier"],
                "description": config["description"],
                "message": f"MODO {season_name.upper().replace('_', ' ')} ATIVADO",
                "current_month": current_month,
                "current_day": current_day,
                "days_until_peak": days_until_peak,
                "is_peak_period": abs(days_until_peak) <= 15,  # Dentro de 15 dias do pico
                "produto_segmento": produto_segmento  # Incluir no contexto
            }
            
            logger.info(
                f"[INFO] Período sazonal detectado: {season_name.upper()} para segmento '{produto_segmento}' "
                f"(Urgência: {config['urgency']}, Multiplicador: {config['multiplier']}x)"
            )
            
            return context
    
    # Não está em período sazonal
    logger.debug(f"Nenhum período sazonal detectado para mês {current_month}")
    return None


def get_seasonal_recommendation(
    base_quantity: float,
    seasonal_context: Optional[Dict] = None
) -> Dict:
    """
    Calcula recomendação de compra ajustada por sazonalidade.
    
    Args:
        base_quantity: Quantidade base calculada (ex: EOQ)
        seasonal_context: Contexto sazonal (se None, detecta automaticamente)
    
    Returns:
        {
            "recommended_quantity": Quantidade recomendada ajustada,
            "base_quantity": Quantidade base original,
            "adjustment_factor": Fator de ajuste aplicado,
            "reasoning": Justificativa da recomendação,
            "urgency": Nível de urgência
        }
    
    Examples:
        >>> get_seasonal_recommendation(1000)
        {
            "recommended_quantity": 2500,
            "base_quantity": 1000,
            "adjustment_factor": 2.5,
            "reasoning": "Ajuste para Volta às Aulas (demanda 2.5x maior)",
            "urgency": "ALTA"
        }
    """
    if seasonal_context is None:
        seasonal_context = detect_seasonal_context()
    
    if seasonal_context is None:
        # Sem ajuste sazonal
        return {
            "recommended_quantity": base_quantity,
            "base_quantity": base_quantity,
            "adjustment_factor": 1.0,
            "reasoning": "Período normal - sem ajuste sazonal",
            "urgency": "NORMAL"
        }
    
    # Aplicar multiplicador sazonal
    multiplier = seasonal_context["multiplier"]
    recommended_quantity = base_quantity * multiplier
    
    # Ajustar se estamos próximos do pico
    if seasonal_context["is_peak_period"]:
        # Aumentar mais 20% se estamos no pico
        recommended_quantity *= 1.2
        peak_adjustment = " (PICO - +20% adicional)"
    else:
        peak_adjustment = ""
    
    reasoning = (
        f"Ajuste para {seasonal_context['description']}: "
        f"demanda {multiplier}x maior{peak_adjustment}. "
        f"Estoque recomendado: {seasonal_context['coverage_days']} dias."
    )
    
    return {
        "recommended_quantity": round(recommended_quantity, 0),
        "base_quantity": base_quantity,
        "adjustment_factor": multiplier * (1.2 if seasonal_context["is_peak_period"] else 1.0),
        "reasoning": reasoning,
        "urgency": seasonal_context["urgency"],
        "season": seasonal_context["season"],
        "days_until_peak": seasonal_context["days_until_peak"]
    }


def get_all_upcoming_seasons(months_ahead: int = 6) -> List[Dict]:
    """
    Retorna todos os períodos sazonais nos próximos N meses.
    
    Args:
        months_ahead: Quantos meses à frente analisar
    
    Returns:
        Lista de períodos sazonais ordenados por proximidade
    
    Examples:
        >>> get_all_upcoming_seasons(6)
        [
            {"season": "volta_as_aulas", "months_until": 0, ...},
            {"season": "pascoa", "months_until": 2, ...},
            ...
        ]
    """
    current_month = datetime.now().month
    upcoming = []
    
    for season_name, config in SEASONAL_PERIODS.items():
        for season_month in config["months"]:
            # Calcular meses até o período
            if season_month >= current_month:
                months_until = season_month - current_month
            else:
                months_until = 12 - current_month + season_month
            
            if months_until <= months_ahead:
                upcoming.append({
                    "season": season_name,
                    "month": season_month,
                    "months_until": months_until,
                    "urgency": config["urgency"],
                    "multiplier": config["multiplier"],
                    "description": config["description"]
                })
    
    # Ordenar por proximidade
    upcoming.sort(key=lambda x: x["months_until"])
    
    return upcoming
