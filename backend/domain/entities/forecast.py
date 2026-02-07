"""
Entity: Forecast

Define a entidade Forecast que representa uma previsão gerada pelo sistema.

Uso:
    from backend.domain.entities import Forecast, ForecastPeriod
    
    forecast = Forecast(
        target="vendas_produto_123",
        period=ForecastPeriod.DAYS_30,
        predicted_value=1500.0,
        confidence=0.85
    )

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4


class ForecastPeriod(str, Enum):
    """Períodos de previsão disponíveis."""
    
    DAYS_7 = "7d"
    DAYS_14 = "14d"
    DAYS_30 = "30d"
    DAYS_60 = "60d"
    DAYS_90 = "90d"


class ForecastMethod(str, Enum):
    """Métodos de previsão disponíveis."""
    
    LINEAR_REGRESSION = "linear_regression"
    POLYNOMIAL = "polynomial"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    PROPHET = "prophet"


@dataclass
class ForecastPoint:
    """
    Um ponto individual na série de previsão.
    
    Attributes:
        date: Data do ponto
        value: Valor previsto
        lower_bound: Limite inferior (intervalo de confiança)
        upper_bound: Limite superior (intervalo de confiança)
    """
    
    date: date
    value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "value": self.value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
        }


@dataclass
class Forecast:
    """
    Entidade que representa uma previsão gerada pelo sistema.
    
    Attributes:
        id: Identificador único
        target: O que está sendo previsto (produto, métrica, etc.)
        period: Período da previsão
        method: Método utilizado
        predicted_value: Valor previsto agregado
        confidence: Nível de confiança (0-1)
        points: Série temporal de pontos previstos
        tenant_id: ID do tenant (multi-tenancy)
        created_at: Data de criação
    
    Example:
        >>> forecast = Forecast(
        ...     target="vendas_loja_1685",
        ...     period=ForecastPeriod.DAYS_30,
        ...     predicted_value=50000.0,
        ...     confidence=0.92
        ... )
        >>> forecast.is_reliable
        True
    """
    
    target: str
    period: ForecastPeriod
    predicted_value: float
    confidence: float = 0.0
    method: ForecastMethod = ForecastMethod.LINEAR_REGRESSION
    id: str = field(default_factory=lambda: str(uuid4()))
    points: List[ForecastPoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    r_squared: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_reliable(self) -> bool:
        """Verifica se a previsão é confiável (>= 80%)."""
        return self.confidence >= 0.80
    
    @property
    def period_days(self) -> int:
        """Retorna o número de dias do período."""
        mapping = {
            ForecastPeriod.DAYS_7: 7,
            ForecastPeriod.DAYS_14: 14,
            ForecastPeriod.DAYS_30: 30,
            ForecastPeriod.DAYS_60: 60,
            ForecastPeriod.DAYS_90: 90,
        }
        return mapping.get(self.period, 30)
    
    def add_point(self, dt: date, value: float, lower: float = None, upper: float = None) -> None:
        """Adiciona um ponto à série de previsão."""
        point = ForecastPoint(date=dt, value=value, lower_bound=lower, upper_bound=upper)
        self.points.append(point)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a previsão para dicionário."""
        return {
            "id": self.id,
            "target": self.target,
            "period": self.period.value,
            "method": self.method.value,
            "predicted_value": self.predicted_value,
            "confidence": self.confidence,
            "r_squared": self.r_squared,
            "points": [p.to_dict() for p in self.points],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self) -> str:
        return f"Forecast(target='{self.target}', value={self.predicted_value:.2f}, confidence={self.confidence:.2%})"
