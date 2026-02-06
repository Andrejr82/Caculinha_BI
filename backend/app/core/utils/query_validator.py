"""
Query Validator - Validador de queries Parquet.

Este módulo fornece validação robusta de queries antes da execução,
incluindo verificação de colunas, tipos e timeout.

Funcionalidades:
- Validação de colunas antes de filtrar
- Tratamento de valores None/null
- Timeout para queries longas
- Mensagens de erro user-friendly

Autor: Code Agent
Data: 2025-10-17
"""

import logging
import signal
from typing import List, Dict, Any, Optional, Callable
from contextlib import contextmanager
import pandas as pd

logger = logging.getLogger(__name__)


class QueryTimeout(Exception):
    """Exceção levantada quando query excede timeout."""
    pass


class QueryValidator:
    """
    Validador de queries com timeout e verificação de integridade.
    """

    def __init__(self, default_timeout: int = 30):
        """
        Inicializa o validador.

        Args:
            default_timeout: Timeout padrão em segundos
        """
        self.default_timeout = default_timeout

    @contextmanager
    def timeout_context(self, seconds: int):
        """
        Context manager para timeout de queries.

        Args:
            seconds: Tempo máximo de execução em segundos

        Raises:
            QueryTimeout: Se a query exceder o tempo limite
        """
        def timeout_handler(signum, frame):
            raise QueryTimeout(f"Query excedeu o tempo limite de {seconds} segundos")

        # Configurar handler (apenas em sistemas Unix-like)
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        except AttributeError:
            # Windows não suporta SIGALRM, executar sem timeout
            logger.warning("Timeout não suportado nesta plataforma")
            yield

    def validate_columns_in_dataframe(
        self,
        df: pd.DataFrame,
        required_columns: List[str],
        table_name: str = "DataFrame"
    ) -> tuple[bool, List[str]]:
        """
        Valida se colunas existem no DataFrame.

        Args:
            df: DataFrame a validar
            required_columns: Lista de colunas obrigatórias
            table_name: Nome da tabela (para mensagens de erro)

        Returns:
            Tupla (is_valid, missing_columns)
        """
        df_columns = set(df.columns)
        required_set = set(required_columns)

        missing_columns = list(required_set - df_columns)

        if missing_columns:
            logger.error(
                f"Validação falhou para '{table_name}': "
                f"Colunas faltantes: {missing_columns}"
            )
            return False, missing_columns

        logger.debug(f"Todas as colunas obrigatórias presentes em '{table_name}'")
        return True, []

    def validate_filter_column(
        self,
        df: pd.DataFrame,
        column_name: str,
        table_name: str = "DataFrame"
    ) -> bool:
        """
        Valida se uma coluna existe antes de aplicar filtro.

        Args:
            df: DataFrame
            column_name: Nome da coluna
            table_name: Nome da tabela

        Returns:
            True se a coluna existe
        """
        if column_name not in df.columns:
            logger.error(
                f"Coluna '{column_name}' não encontrada em '{table_name}'. "
                f"Colunas disponíveis: {list(df.columns)}"
            )
            return False

        return True

    def handle_null_values(
        self,
        df: pd.DataFrame,
        column_name: str,
        strategy: str = "drop",
        fill_value: Any = None
    ) -> pd.DataFrame:
        """
        Trata valores nulos em uma coluna.

        Args:
            df: DataFrame
            column_name: Nome da coluna
            strategy: Estratégia ('drop', 'fill', 'keep')
            fill_value: Valor para preencher (se strategy='fill')

        Returns:
            DataFrame com valores nulos tratados
        """
        if column_name not in df.columns:
            logger.warning(f"Coluna '{column_name}' não encontrada, retornando DataFrame original")
            return df

        null_count = df[column_name].isna().sum()

        if null_count > 0:
            logger.info(f"Encontrados {null_count} valores nulos em '{column_name}'")

            if strategy == "drop":
                df = df.dropna(subset=[column_name])
                logger.info(f"Removidas {null_count} linhas com valores nulos")

            elif strategy == "fill":
                if fill_value is None:
                    # Estratégia padrão baseada no tipo
                    if df[column_name].dtype in ['float64', 'int64']:
                        fill_value = 0
                    else:
                        fill_value = ""

                df[column_name].fillna(fill_value, inplace=True)
                logger.info(f"Preenchidos {null_count} valores nulos com '{fill_value}'")

            elif strategy == "keep":
                logger.info(f"Mantendo {null_count} valores nulos")

        return df

    def safe_filter(
        self,
        df: pd.DataFrame,
        filter_func: Callable[[pd.DataFrame], pd.DataFrame],
        error_message: str = "Erro ao aplicar filtro"
    ) -> pd.DataFrame:
        """
        Aplica filtro de forma segura com tratamento de erros.

        Args:
            df: DataFrame
            filter_func: Função de filtro
            error_message: Mensagem de erro personalizada

        Returns:
            DataFrame filtrado ou original em caso de erro
        """
        try:
            return filter_func(df)
        except KeyError as e:
            logger.error(f"{error_message}: Coluna não encontrada - {e}")
            return df
        except Exception as e:
            logger.error(f"{error_message}: {e}")
            return df

    def execute_with_timeout(
        self,
        func: Callable,
        timeout: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Executa função com timeout.

        Args:
            func: Função a executar
            timeout: Tempo limite em segundos (usa default se None)
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            Resultado da função

        Raises:
            QueryTimeout: Se exceder o tempo limite
        """
        if timeout is None:
            timeout = self.default_timeout

        try:
            with self.timeout_context(timeout):
                return func(*args, **kwargs)
        except QueryTimeout as e:
            logger.error(f"Query timeout: {e}")
            raise

    def validate_and_convert_types(
        self,
        df: pd.DataFrame,
        column_types: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Valida e converte tipos de colunas.

        Args:
            df: DataFrame
            column_types: Dict {column_name: desired_type}
                Tipos suportados: 'int', 'float', 'str', 'datetime'

        Returns:
            DataFrame com tipos convertidos
        """
        df_copy = df.copy()

        for column, desired_type in column_types.items():
            if column not in df_copy.columns:
                logger.warning(f"Coluna '{column}' não encontrada para conversão de tipo")
                continue

            try:
                if desired_type == 'int':
                    df_copy[column] = pd.to_numeric(df_copy[column], errors='coerce').fillna(0).astype(int)

                elif desired_type == 'float':
                    df_copy[column] = pd.to_numeric(df_copy[column], errors='coerce').fillna(0.0)

                elif desired_type == 'str':
                    df_copy[column] = df_copy[column].astype(str).replace('nan', '')

                elif desired_type == 'datetime':
                    df_copy[column] = pd.to_datetime(df_copy[column], errors='coerce')

                else:
                    logger.warning(f"Tipo desconhecido '{desired_type}' para coluna '{column}'")

                logger.debug(f"Coluna '{column}' convertida para '{desired_type}'")

            except Exception as e:
                logger.error(f"Erro ao converter coluna '{column}' para '{desired_type}': {e}")

        return df_copy

    def get_user_friendly_error(self, error: Exception) -> str:
        """
        Converte exceção em mensagem user-friendly.

        Args:
            error: Exceção capturada

        Returns:
            Mensagem de erro formatada para o usuário
        """
        error_type = type(error).__name__

        # Mapeamento de erros técnicos para mensagens amigáveis
        error_messages = {
            'FileNotFoundError': 'Arquivo de dados não encontrado. Verifique se os dados foram carregados corretamente.',
            'PermissionError': 'Sem permissão para acessar o arquivo de dados.',
            'KeyError': 'Coluna especificada não existe nos dados. Verifique os nomes das colunas.',
            'ValueError': 'Valor inválido encontrado nos dados. Verifique os filtros aplicados.',
            'TypeError': 'Tipo de dado incompatível na operação.',
            'QueryTimeout': 'A consulta demorou muito tempo. Tente usar filtros mais específicos.',
            'ParserError': 'Erro ao ler o arquivo de dados. O arquivo pode estar corrompido.',
            'MemoryError': 'Memória insuficiente para processar a consulta. Reduza o volume de dados.',
        }

        # Retornar mensagem personalizada ou genérica
        base_message = error_messages.get(error_type, 'Erro ao processar a consulta.')

        return f"{base_message} (Detalhes técnicos: {str(error)})"


# Instância global
_validator = QueryValidator()


def safe_convert_types(df: pd.DataFrame, column_types: Dict[str, str]) -> pd.DataFrame:
    """Compat shim: nome legado esperado por alguns testes/scripts.

    Encaminha para `validate_and_convert_types` do `QueryValidator`.
    """
    return _validator.validate_and_convert_types(df, column_types)

# Funções auxiliares para uso direto
def validate_columns(df: pd.DataFrame, required_columns: List[str], table_name: str = "DataFrame") -> tuple[bool, List[str]]:
    """Valida colunas em DataFrame."""
    return _validator.validate_columns_in_dataframe(df, required_columns, table_name)


def handle_nulls(df: pd.DataFrame, column: str, strategy: str = "drop", fill_value: Any = None) -> pd.DataFrame:
    """Trata valores nulos."""
    return _validator.handle_null_values(df, column, strategy, fill_value)


def safe_filter(df: pd.DataFrame, filter_func: Callable, error_msg: str = "Erro ao filtrar") -> pd.DataFrame:
    """Aplica filtro com segurança."""
    return _validator.safe_filter(df, filter_func, error_msg)


def get_friendly_error(error: Exception) -> str:
    """Converte erro em mensagem amigável."""
    return _validator.get_user_friendly_error(error)


if __name__ == "__main__":
    # Testes básicos
    logging.basicConfig(level=logging.INFO)

    # Teste de validação de colunas
    df_test = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })

    is_valid, missing = validate_columns(df_test, ['col1', 'col2', 'col3'])
    print(f"Validação: {is_valid}, Faltantes: {missing}")

    # Teste de tratamento de nulos
    df_test['col3'] = [1, None, 3]
    df_clean = handle_nulls(df_test, 'col3', strategy='fill', fill_value=0)
    print(f"Nulos tratados: {df_clean['col3'].tolist()}")
