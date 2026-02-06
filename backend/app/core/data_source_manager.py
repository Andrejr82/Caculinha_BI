"""
Data Source Manager - Acesso centralizado aos dados Parquet
Adaptado para Agent Solution BI: admmat.parquet
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.core.parquet_cache import cache

logger = logging.getLogger(__name__)

# Constantes: Arquivos de dados
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MAIN_DATA_FILE = PROJECT_ROOT / "data" / "parquet" / "admmat.parquet"


class ParquetDataSource:
    """Acesso centralizado ao arquivo admmat.parquet."""

    def __init__(self):
        self._connected = False
        self._df_cache: Optional[pd.DataFrame] = None

        # Path local para arquivo Parquet
        self.file_path = MAIN_DATA_FILE
        logger.info(f"[FILE] Usando arquivo: {self.file_path}")


    def connect(self) -> bool:
        """Verifica se arquivo Parquet existe."""
        if self.file_path.exists():
            self._connected = True
            logger.info(f"[OK] Parquet conectado: {self.file_path}")
            return True

        logger.error(f"[ERROR] Arquivo não encontrado: {self.file_path}")
        self._connected = False
        return False

    def is_connected(self) -> bool:
        """Verifica se está conectado."""
        return self._connected and self.file_path.exists()

    def _load_data(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Carrega os dados do arquivo Parquet usando ParquetCache global.
        [OK]: OTIMIZADO: Usa cache global ao invés de cache local.
        """
        try:
            # Usar ParquetCache global (já retorna Polars DataFrame ou Pandas DataFrame dependendo da config)
            df_polars = cache.get_dataframe("admmat.parquet")

            # Converter para Pandas (necessário para compatibilidade com ferramentas existentes)
            if hasattr(df_polars, 'to_pandas'):
                df = df_polars.to_pandas()
            elif hasattr(df_polars, 'df'): # DuckDB Relation
                df = df_polars.df()
            elif isinstance(df_polars, pd.DataFrame):
                df = df_polars
            else:
                # Tentar converter qualquer outro formato ou falhar graciosamente
                df = pd.DataFrame(df_polars)

            logger.info(f"[OK] Dados obtidos do cache: {df.shape}")
            return df

        except FileNotFoundError as e:
            logger.error(f"[ERROR] ERRO CRÍTICO: Arquivo não encontrado: {self.file_path}")
            raise
        except Exception as e:
            logger.error(f"[ERROR] ERRO ao ler Parquet: {e}")
            raise

    def get_data(self, limit: int = None) -> pd.DataFrame:
        """
        Obtém todos os dados ou limitados.
        SECURITY 2025: Aplica Row-Level Security (RLS) automaticamente.
        """
        df = self._load_data()
        
        # SECURITY: Apply RLS - Filter by user segments
        from app.core.context import get_current_user_segments
        
        allowed_segments = get_current_user_segments()
        
        if allowed_segments and "*" not in allowed_segments:
            # User has restricted access - filter by segment
            if 'NOMESEGMENTO' in df.columns:
                logger.info(f"[RLS] Aplicando filtro de segmento: {allowed_segments}")
                df = df[df['NOMESEGMENTO'].isin(allowed_segments)]
            else:
                logger.warning("[RLS] Coluna NOMESEGMENTO não encontrada - RLS não aplicado!")
        else:
            logger.info(f"[RLS] Usuário com acesso total (segments={allowed_segments})")
        
        if limit and not df.empty:
            df = df.head(limit)
        return df

    def search(self, column: str, value: str, limit: int = 10) -> pd.DataFrame:
        """Busca em uma coluna."""
        try:
            df = self._load_data()
            if df.empty or column not in df.columns:
                return pd.DataFrame()

            # Busca case-insensitive
            mask = df[column].astype(str).str.contains(value, case=False, na=False)
            result = df[mask].head(limit)
            return result

        except Exception as e:
            logger.error(f"Erro ao buscar: {e}")
            return pd.DataFrame()

    def get_filtered_data(
        self, filters: Dict[str, Any], limit: int = None
    ) -> pd.DataFrame:
        """Busca com filtros exatos."""
        try:
            df = self._load_data()
            if df.empty:
                return pd.DataFrame()

            for col, value in filters.items():
                if col in df.columns:
                    col_dtype = df[col].dtype
                    try:
                        if pd.api.types.is_numeric_dtype(col_dtype) and isinstance(value, str):
                            converted_value = pd.to_numeric(value, errors='raise')
                            df = df[df[col] == converted_value]
                        elif pd.api.types.is_datetime64_any_dtype(col_dtype) and isinstance(value, str):
                            converted_value = pd.to_datetime(value, errors='raise')
                            df = df[df[col] == converted_value]
                        else:
                            df = df[df[col] == value]
                    except (ValueError, TypeError):
                        df = df[df[col].astype(str).str.lower() == str(value).lower()]
                else:
                    logger.warning(f"Coluna '{col}' não encontrada")
                    return pd.DataFrame()

            if limit:
                df = df.head(limit)

            return df
        except Exception as e:
            logger.error(f"Erro ao filtrar: {e}")
            return pd.DataFrame()

    def get_columns(self) -> List[str]:
        """Retorna lista de colunas de forma otimizada (sem carregar dados)."""
        try:
            from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
            adapter = get_duckdb_adapter()
            # Usar DESCRIBE SELECT * para pegar colunas sem materializar
            path = str(self.file_path).replace("\\", "/")
            schema_df = adapter.query(f"DESCRIBE SELECT * FROM read_parquet('{path}')")
            return schema_df['column_name'].tolist()
        except Exception as e:
            logger.error(f"[ERROR] Falha ao obter colunas via DuckDB: {e}. Tentando fallback.")
            try:
                # Fallback: ler apenas schema com pandas
                df_schema = pd.read_parquet(self.file_path, engine='pyarrow') # read_parquet lê schema primeiro
                return df_schema.columns.tolist()
            except Exception as e2:
                logger.error(f"[ERROR] Falha total ao obter colunas: {e2}")
                return []

    def get_shape(self) -> tuple:
        """Retorna dimensões dos dados."""
        df = self._load_data()
        return df.shape if not df.empty else (0, 0)

    def get_info(self) -> Dict[str, Any]:
        """Retorna informações sobre os dados."""
        df = self._load_data()
        if df.empty:
            return {"status": "sem_dados"}

        return {
            "file": str(self.file_path),
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": {k: str(v) for k, v in df.dtypes.to_dict().items()},
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
        }


class DataSourceManager:
    """
    Gerenciador de fonte de dados centralizado.
    Acessa: data/parquet/admmat.parquet
    """

    def __init__(self):
        self._source = ParquetDataSource()
        self._source.connect()

    def get_data(
        self, table_name: str = None, limit: int = None, source: str = None
    ) -> pd.DataFrame:
        """Obtém dados (table_name é ignorado)."""
        return self._source.get_data(limit)

    def search_data(
        self,
        table_name: str = None,
        column: str = None,
        value: str = None,
        limit: int = 10,
        source: str = None,
    ) -> pd.DataFrame:
        """Busca dados em coluna especificada."""
        if not column or not value:
            return pd.DataFrame()
        return self._source.search(column, value, limit)

    def get_filtered_data(
        self,
        table_name: str = None,
        filters: Dict[str, Any] = None,
        limit: int = None,
        source: str = None,
    ) -> pd.DataFrame:
        """Busca com filtros."""
        if not filters:
            return pd.DataFrame()
        return self._source.get_filtered_data(filters, limit)

    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Não suportado para Parquet."""
        return []

    def get_available_sources(self) -> List[str]:
        """Retorna fontes disponíveis."""
        if self._source.is_connected():
            return ["admmat_parquet"]
        return []

    def get_source_info(self) -> Dict[str, Any]:
        """Retorna informações da fonte."""
        return self._source.get_info()

    def get_columns(self) -> List[str]:
        """Retorna lista de colunas disponíveis."""
        return self._source.get_columns()


# Instância global singleton
_data_manager_instance: Optional[DataSourceManager] = None


def get_data_manager() -> DataSourceManager:
    """Retorna instância singleton do DataSourceManager."""
    global _data_manager_instance
    if _data_manager_instance is None:
        _data_manager_instance = DataSourceManager()
    return _data_manager_instance
