"""
Value Object: TimeRange

Intervalo de tempo imutável para queries e análises.

Uso:
    from backend.domain.value_objects import TimeRange
    
    range_30d = TimeRange.last_n_days(30)
    range_custom = TimeRange(start=date(2026, 1, 1), end=date(2026, 1, 31))

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass(frozen=True)
class TimeRange:
    """
    Value Object imutável para intervalo de tempo.
    
    Attributes:
        start: Data de início
        end: Data de fim
    
    Example:
        >>> range = TimeRange.last_n_days(30)
        >>> range.days
        30
        >>> range.is_valid
        True
    """
    
    start: date
    end: date
    
    def __post_init__(self) -> None:
        """Valida o intervalo no momento da criação."""
        if self.start > self.end:
            raise ValueError(
                f"Data de início ({self.start}) não pode ser posterior à data de fim ({self.end})"
            )
    
    @classmethod
    def last_n_days(cls, n: int) -> "TimeRange":
        """Cria um TimeRange dos últimos N dias até hoje."""
        today = date.today()
        start = today - timedelta(days=n)
        return cls(start=start, end=today)
    
    @classmethod
    def last_week(cls) -> "TimeRange":
        """Cria um TimeRange da última semana."""
        return cls.last_n_days(7)
    
    @classmethod
    def last_month(cls) -> "TimeRange":
        """Cria um TimeRange do último mês (30 dias)."""
        return cls.last_n_days(30)
    
    @classmethod
    def last_quarter(cls) -> "TimeRange":
        """Cria um TimeRange do último trimestre (90 dias)."""
        return cls.last_n_days(90)
    
    @classmethod
    def this_month(cls) -> "TimeRange":
        """Cria um TimeRange do mês corrente."""
        today = date.today()
        start = today.replace(day=1)
        return cls(start=start, end=today)
    
    @property
    def days(self) -> int:
        """Retorna o número de dias no intervalo."""
        return (self.end - self.start).days
    
    @property
    def is_valid(self) -> bool:
        """Verifica se o intervalo é válido (start <= end)."""
        return self.start <= self.end
    
    def contains(self, dt: date) -> bool:
        """Verifica se uma data está contida no intervalo."""
        return self.start <= dt <= self.end
    
    def overlaps(self, other: "TimeRange") -> bool:
        """Verifica se há sobreposição com outro intervalo."""
        return self.start <= other.end and other.start <= self.end
    
    def to_sql_filter(self, column: str) -> str:
        """Gera uma cláusula SQL para filtrar por este intervalo."""
        return f"{column} BETWEEN '{self.start}' AND '{self.end}'"
    
    def __str__(self) -> str:
        return f"{self.start} to {self.end}"
    
    def __repr__(self) -> str:
        return f"TimeRange(start={self.start}, end={self.end}, days={self.days})"
