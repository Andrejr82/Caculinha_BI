"""
Sistema Robusto de Validação e Auto-Correção de Colunas
========================================================

Previne erros como ColumnNotFoundError do Polars antes da execução de queries.

Funcionalidades:
1. Validação preditiva de colunas antes da execução
2. Auto-correção de nomes de colunas (fuzzy matching)
3. Sugestões inteligentes para erros
4. Cache de validações para performance
5. Integração com column_mapping.py e Polars exceptions

Autor: Claude Code + Context7 Docs
Data: 2025-10-27
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from difflib import get_close_matches
from functools import lru_cache

# Importações do projeto (AJUSTADO PARA BACKEND)
from app.infrastructure.data.config.column_mapping import (
    COLUMN_MAP,
    COLUMN_INFO,
    normalize_column_name,
    ESSENTIAL_COLUMNS
)

logger = logging.getLogger(__name__)

# ==================== CONFIGURAÇÕES ====================

# Similaridade mínima para sugestões (0.0 a 1.0)
SIMILARITY_THRESHOLD = 0.6

# Número máximo de sugestões
MAX_SUGGESTIONS = 3

# Cache de validações (evita re-validar mesmas colunas)
VALIDATION_CACHE = {}


# ==================== EXCEÇÕES CUSTOMIZADAS ====================

class ColumnValidationError(Exception):
    """Erro de validação de coluna com sugestões."""

    def __init__(self, column: str, suggestions: List[str] = None, available_columns: List[str] = None):
        self.column = column
        self.suggestions = suggestions or []
        self.available_columns = available_columns or []

        msg = f"Coluna '{column}' não encontrada no DataFrame."

        if self.suggestions:
            msg += f"\n\nSugestões:\n" + "\n".join(f"  - {s}" for s in self.suggestions[:MAX_SUGGESTIONS])

        if len(self.available_columns) <= 20:
            msg += f"\n\nColunas disponíveis:\n" + "\n".join(f"  - {c}" for c in sorted(self.available_columns)[:20])
        else:
            msg += f"\n\n{len(self.available_columns)} colunas disponíveis (use list_columns() para ver todas)"

        super().__init__(msg)


# ==================== FUNÇÕES DE VALIDAÇÃO ====================

@lru_cache(maxsize=128)
def get_available_columns_cached(file_path: str) -> Tuple[str, ...]:
    """
    Retorna colunas disponíveis no Parquet (com cache).

    Args:
        file_path: Caminho do arquivo Parquet

    Returns:
        Tupla com nomes das colunas (imutável para cache)
    """
    try:
        import polars as pl

        # Ler apenas o schema (sem carregar dados)
        df_schema = pl.read_parquet_schema(file_path)
        columns = tuple(df_schema.keys())

        logger.debug(f"Schema lido: {len(columns)} colunas encontradas")
        return columns

    except Exception as e:
        logger.error(f"Erro ao ler schema do Parquet: {e}")
        # Fallback para colunas essenciais conhecidas
        return tuple(ESSENTIAL_COLUMNS)


def validate_column(
    column: str,
    available_columns: List[str],
    auto_correct: bool = True,
    raise_on_error: bool = False
) -> Tuple[bool, Optional[str], List[str]]:
    """
    Valida se uma coluna existe no DataFrame.

    Args:
        column: Nome da coluna a validar
        available_columns: Lista de colunas disponíveis no DataFrame
        auto_correct: Se True, tenta corrigir automaticamente
        raise_on_error: Se True, levanta exceção em vez de retornar erro

    Returns:
        Tupla (is_valid, corrected_name, suggestions)
        - is_valid: True se coluna é válida/corrigível
        - corrected_name: Nome corrigido (ou None se não encontrado)
        - suggestions: Lista de sugestões alternativas

    Raises:
        ColumnValidationError: Se raise_on_error=True e coluna inválida
    """
    # Verificação rápida de cache
    cache_key = f"{column}:{','.join(sorted(available_columns))}"
    if cache_key in VALIDATION_CACHE:
        return VALIDATION_CACHE[cache_key]

    # 1. Verificar se coluna já existe (case-sensitive)
    if column in available_columns:
        result = (True, column, [])
        VALIDATION_CACHE[cache_key] = result
        return result

    # 2. Tentar normalizar usando COLUMN_MAP
    normalized = normalize_column_name(column)
    if normalized in available_columns:
        logger.info(f"[OK] Coluna '{column}' normalizada para '{normalized}'")
        result = (True, normalized, [normalized])
        VALIDATION_CACHE[cache_key] = result
        return result

    # 3. Tentar match case-insensitive
    column_lower = column.lower()
    for col in available_columns:
        if col.lower() == column_lower:
            logger.info(f"[OK] Coluna '{column}' encontrada com case diferente: '{col}'")
            result = (True, col, [col])
            VALIDATION_CACHE[cache_key] = result
            return result

    # 4. Se auto_correct, buscar similares
    suggestions = []
    if auto_correct:
        # Fuzzy matching usando difflib
        suggestions = get_close_matches(
            column.lower(),
            [c.lower() for c in available_columns],
            n=MAX_SUGGESTIONS,
            cutoff=SIMILARITY_THRESHOLD
        )

        # Mapear de volta para nomes originais
        suggestions = [
            next(c for c in available_columns if c.lower() == s)
            for s in suggestions
        ]

        # Adicionar sugestões do COLUMN_MAP
        for legacy_name, real_name in COLUMN_MAP.items():
            if column.upper() == legacy_name and real_name in available_columns:
                if real_name not in suggestions:
                    suggestions.insert(0, real_name)

        logger.warning(f"[WARN] Coluna '{column}' não encontrada. Sugestões: {suggestions}")

    # 5. Retornar resultado ou levantar exceção
    if raise_on_error:
        raise ColumnValidationError(column, suggestions, available_columns)

    result = (False, None, suggestions)
    VALIDATION_CACHE[cache_key] = result
    return result


def validate_columns(
    columns: List[str],
    available_columns: List[str],
    auto_correct: bool = True
) -> Dict[str, Any]:
    """
    Valida múltiplas colunas de uma vez.
    """
    valid = []
    invalid = []
    corrected = {}
    suggestions_map = {}

    for col in columns:
        is_valid, corrected_name, suggestions = validate_column(
            col, available_columns, auto_correct, raise_on_error=False
        )

        if is_valid:
            valid.append(corrected_name)
            if col != corrected_name:
                corrected[col] = corrected_name
        else:
            invalid.append(col)
            if suggestions:
                suggestions_map[col] = suggestions

    return {
        "valid": valid,
        "invalid": invalid,
        "corrected": corrected,
        "suggestions": suggestions_map,
        "all_valid": len(invalid) == 0
    }


def safe_select_columns(
    df: Any,  # pl.DataFrame ou pl.LazyFrame
    columns: List[str],
    auto_correct: bool = True,
    drop_invalid: bool = False
) -> Tuple[Any, Dict[str, Any]]:
    """
    Versão segura de df.select() que valida e corrige colunas antes.
    """
    available = df.columns

    validation = validate_columns(columns, available, auto_correct)

    # Se tem inválidas e não deve dropar, erro
    if validation["invalid"] and not drop_invalid:
        first_invalid = validation["invalid"][0]
        raise ColumnValidationError(
            first_invalid,
            validation["suggestions"].get(first_invalid, []),
            available
        )

    # Selecionar apenas colunas válidas
    valid_cols = validation["valid"]

    if not valid_cols:
        raise ValueError("Nenhuma coluna válida para selecionar!")

    # Aplicar select com colunas corrigidas
    df_result = df.select(valid_cols)

    logger.info(f"[OK] safe_select: {len(valid_cols)}/{len(columns)} colunas selecionadas")
    if validation["corrected"]:
        logger.info(f"   Correções: {validation['corrected']}")
    if validation["invalid"]:
        logger.warning(f"   Ignoradas: {validation['invalid']}")

    return df_result, validation


def extract_columns_from_query(query_code: str) -> List[str]:
    """
    Extrai nomes de colunas de código Python/Polars.
    """
    columns = set()

    # Padrão 1: pl.col("coluna")
    for match in re.finditer(r'pl\.col\(["\']([^"\']+)["\']\)', query_code):
        columns.add(match.group(1))

    # Padrão 2: df["coluna"]
    for match in re.finditer(r'\[["\']([^"\']+)["\']\]', query_code):
        columns.add(match.group(1))

    # Padrão 3: .select(["col1", "col2"])
    for match in re.finditer(r'\.select\(\[(.*?)\]\)', query_code):
        cols_str = match.group(1)
        for col in re.findall(r'["\']([^"\']+)["\']', cols_str):
            columns.add(col)

    # Padrão 4: .group_by("coluna")
    for match in re.finditer(r'\.group_by\(["\']([^"\']+)["\']\)', query_code):
        columns.add(match.group(1))

    # Padrão 5: .sort("coluna")
    for match in re.finditer(r'\.sort\(["\']([^"\']+)["\']\)', query_code):
        columns.add(match.group(1))

    return list(columns)


def validate_query_code(
    query_code: str,
    available_columns: List[str],
    auto_correct: bool = True
) -> Dict[str, Any]:
    """
    Valida código de query antes da execução.
    """
    # Extrair colunas do código
    columns_used = extract_columns_from_query(query_code)

    if not columns_used:
        logger.warning("[WARN] Nenhuma coluna detectada no código da query")
        return {
            "valid": True,
            "original_code": query_code,
            "corrected_code": query_code,
            "columns_used": [],
            "validation": {"valid": [], "invalid": [], "corrected": {}, "suggestions": {}, "all_valid": True}
        }

    # Validar colunas
    validation = validate_columns(columns_used, available_columns, auto_correct)

    # Se auto_correct, substituir no código
    corrected_code = query_code
    if auto_correct and validation["corrected"]:
        for old_name, new_name in validation["corrected"].items():
            # Substituir todas as ocorrências (com aspas)
            corrected_code = corrected_code.replace(f'"{old_name}"', f'"{new_name}"')
            corrected_code = corrected_code.replace(f"'{old_name}'", f"'{new_name}'")

        logger.info(f"[OK] Código corrigido: {len(validation['corrected'])} substituições")

    return {
        "valid": validation["all_valid"],
        "original_code": query_code,
        "corrected_code": corrected_code,
        "columns_used": columns_used,
        "validation": validation
    }


# ==================== FUNÇÕES AUXILIARES ====================

def clear_validation_cache():
    """Limpa cache de validações (útil para testes)."""
    global VALIDATION_CACHE
    VALIDATION_CACHE.clear()
    get_available_columns_cached.cache_clear()
    logger.info("[OK] Cache de validação limpo")
