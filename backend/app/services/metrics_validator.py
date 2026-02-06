"""
Metrics Validator - Truth Contract obrigatório.

Arquitetura Metrics-First - Fase 4
Componente CRÍTICO que garante que apenas métricas válidas sejam enviadas à LLM.

Regra de Ouro:
    Sem passar aqui → LLM não responde

Objetivo:
    Eliminar 90% das alucinações impedindo a LLM de responder sem dados válidos.
"""

import logging
import math
from typing import Any, Dict

logger = logging.getLogger(__name__)


class NoDataError(Exception):
    """
    Levantado quando não há dados para os filtros aplicados.
    
    Tratamento:
        Retornar SystemResponse (não LLM) com sugestão de ampliar critérios.
    """
    pass


class InvalidMetricError(Exception):
    """
    Levantado quando métricas contêm valores inválidos (None, NaN, Inf).
    
    Tratamento:
        Log técnico + resposta genérica ao usuário.
    """
    pass


def validate_metrics(metrics_result: Any) -> None:
    """
    Valida métricas antes de enviar à LLM.
    
    Validações:
    1. Verificar se há dados (row_count > 0)
    2. Verificar métricas nulas
    3. Verificar valores numéricos válidos (não NaN, não Inf)
    4. Verificar dimensões (warning se vazio)
    
    Args:
        metrics_result: Objeto MetricsResult a ser validado
    
    Raises:
        NoDataError: Se não houver dados
        InvalidMetricError: Se métricas forem inválidas
    
    Example:
        >>> try:
        >>>     metrics = metrics_calculator.calculate(intent)
        >>>     validate_metrics(metrics)  # ← OBRIGATÓRIO
        >>> except NoDataError as e:
        >>>     return SystemResponse(message=str(e), type="no_data")
    """
    
    # 1. Verificar se há dados
    if metrics_result.row_count == 0:
        logger.warning("Validação falhou: Nenhum dado encontrado")
        raise NoDataError(
            "Não há dados suficientes para responder com os filtros atuais. "
            "Tente ampliar os critérios de busca (ex: remover filtros específicos, "
            "buscar por categoria ao invés de produto específico)."
        )
    
    # 2. Verificar métricas nulas
    if metrics_result.metrics:
        null_metrics = [
            key for key, value in metrics_result.metrics.items()
            if value is None
        ]
        
        if null_metrics:
            logger.error(f"Validação falhou: Métricas nulas detectadas: {null_metrics}")
            raise InvalidMetricError(
                f"Métricas inválidas detectadas: {', '.join(null_metrics)}. "
                "Verifique os dados de origem."
            )
    
    # 3. Verificar valores numéricos válidos
    if metrics_result.metrics:
        for key, value in metrics_result.metrics.items():
            if isinstance(value, float):
                if math.isnan(value):
                    logger.error(f"Validação falhou: Métrica '{key}' é NaN")
                    raise InvalidMetricError(
                        f"Métrica '{key}' contém valor inválido (NaN)"
                    )
                
                if math.isinf(value):
                    logger.error(f"Validação falhou: Métrica '{key}' é Infinito")
                    raise InvalidMetricError(
                        f"Métrica '{key}' contém valor inválido (Infinito)"
                    )
    
    # 4. Verificar dimensões (warning se vazio, não erro)
    if hasattr(metrics_result, 'dimensions'):
        if metrics_result.dimensions is not None and len(metrics_result.dimensions) == 0:
            logger.warning(
                "Métricas sem dimensões - resposta pode ser genérica. "
                "Considere adicionar agrupamentos (GROUP BY) na query."
            )
    
    # [OK] Se chegou aqui, métricas são válidas
    logger.info(
        f"[OK] Métricas validadas com sucesso: "
        f"{metrics_result.row_count} linhas, "
        f"{len(metrics_result.metrics)} métricas"
    )


def validate_metrics_safe(metrics_result: Any) -> bool:
    """
    Versão segura de validate_metrics que retorna bool ao invés de levantar exceção.
    
    Útil para validações condicionais onde você quer apenas verificar sem interromper.
    
    Args:
        metrics_result: Objeto MetricsResult a ser validado
    
    Returns:
        True se válido, False se inválido
    
    Example:
        >>> if validate_metrics_safe(metrics):
        >>>     # Prosseguir com LLM
        >>> else:
        >>>     # Retornar resposta do sistema
    """
    try:
        validate_metrics(metrics_result)
        return True
    except (NoDataError, InvalidMetricError) as e:
        logger.debug(f"Validação falhou (safe mode): {e}")
        return False


def get_validation_summary(metrics_result: Any) -> Dict[str, Any]:
    """
    Retorna um resumo da validação sem levantar exceções.
    
    Útil para debugging e logging.
    
    Args:
        metrics_result: Objeto MetricsResult a ser validado
    
    Returns:
        Dicionário com status da validação e detalhes
    
    Example:
        >>> summary = get_validation_summary(metrics)
        >>> logger.info(f"Validação: {summary}")
    """
    summary = {
        "is_valid": False,
        "has_data": False,
        "row_count": 0,
        "metrics_count": 0,
        "dimensions_count": 0,
        "issues": []
    }
    
    try:
        # Verificar dados
        if metrics_result.row_count > 0:
            summary["has_data"] = True
            summary["row_count"] = metrics_result.row_count
        else:
            summary["issues"].append("no_data")
        
        # Verificar métricas
        if metrics_result.metrics:
            summary["metrics_count"] = len(metrics_result.metrics)
            
            # Verificar nulos
            null_metrics = [
                key for key, value in metrics_result.metrics.items()
                if value is None
            ]
            if null_metrics:
                summary["issues"].append(f"null_metrics: {null_metrics}")
            
            # Verificar NaN/Inf
            for key, value in metrics_result.metrics.items():
                if isinstance(value, float):
                    if math.isnan(value):
                        summary["issues"].append(f"nan_metric: {key}")
                    if math.isinf(value):
                        summary["issues"].append(f"inf_metric: {key}")
        
        # Verificar dimensões
        if hasattr(metrics_result, 'dimensions') and metrics_result.dimensions:
            summary["dimensions_count"] = len(metrics_result.dimensions)
        
        # Determinar se é válido
        summary["is_valid"] = len(summary["issues"]) == 0 and summary["has_data"]
        
    except Exception as e:
        summary["issues"].append(f"validation_error: {str(e)}")
    
    return summary
