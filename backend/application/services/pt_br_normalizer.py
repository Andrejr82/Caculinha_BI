"""
PT-BR Normalizer — Utilidade de Normalização de Texto

Responsável por limpar, normalizar e tokenizar textos em português brasileiro 
para indexação e busca no catálogo de produtos.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import re
import unicodedata
from typing import List, Set
import structlog

logger = structlog.get_logger(__name__)

class PTBRNormalizer:
    """
    Utilitário para processamento de texto pt-BR.
    """
    
    # Unidades comuns para normalização específica
    UNIT_MAPPING = {
        r'\bkg\b': 'kilograma',
        r'\bkilos\b': 'kilograma',
        r'\bg\b': 'grama',
        r'\bgr\b': 'grama',
        r'\bml\b': 'mililitro',
        r'\bl\b': 'litro',
        r'\bmt\b': 'metro',
        r'\bmts\b': 'metro',
        r'\bcm\b': 'centimetro',
        r'\bun\b': 'unidade',
    }

    # Stopwords básicas pt-BR
    STOPWORDS: Set[str] = {
        'de', 'do', 'da', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'em', 'um', 'uma', 
        'uns', 'umas', 'com', 'para', 'por', 'ou', 'e', 'a', 'o', 'os', 'as'
    }

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalização para string individual."""
        if not text or not isinstance(text, str):
            return ""
        text = text.lower()
        text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    @classmethod
    def normalize_series(cls, series: "pd.Series") -> "pd.Series":
        """
        Normalização vetorizada para Pandas Series.
        Muito mais rápida para 1M+ registros.
        """
        import pandas as pd
        # 1. Lowercase e remover nulos
        s = series.fillna("").str.lower()
        
        # 2. Remover acentos (usando normalize do pandas)
        s = s.str.normalize('NFD').str.encode('ascii', errors='ignore').str.decode('utf-8')
        
        # 3. Remover caracteres especiais e espaços extras
        s = s.str.replace(r'[^a-z0-9\s]', ' ', regex=True)
        s = s.str.replace(r'\s+', ' ', regex=True).str.strip()
        
        return s

    @classmethod
    def tokenize(cls, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokeniza o texto normalizado.
        """
        normalized = cls.normalize_text(text)
        tokens = normalized.split()
        
        if remove_stopwords:
            tokens = [t for t in tokens if t not in cls.STOPWORDS]
            
        return tokens

    @classmethod
    def prepare_searchable_text(cls, fields: List[str]) -> str:
        """
        Concatena múltiplos campos em um texto único normalizado para indexação.
        """
        combined = " ".join([str(f) for f in fields if f])
        return cls.normalize_text(combined)
