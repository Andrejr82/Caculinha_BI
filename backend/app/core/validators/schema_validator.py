"""
SchemaValidator - Validador de schemas Parquet.

Este módulo fornece validação robusta de schemas Parquet contra
o catálogo de dados corporativo (catalog_focused.json).

Funcionalidades:
- Validação de tipos de dados
- Detecção de incompatibilidades de schema
- Mensagens de erro contextualizadas
- Verificação de colunas obrigatórias

Autor: Code Agent
Data: 2025-10-17
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Validador de schemas Parquet contra catálogo corporativo.

    Attributes:
        catalog (Dict): Catálogo de dados carregado do JSON
        catalog_path (Path): Caminho para o arquivo de catálogo
    """

    # Mapeamento de tipos Parquet para tipos Python/Pandas
    TYPE_MAPPING = {
        'int64': ['int64', 'int32', 'int16', 'int8'],
        'float64': ['float64', 'float32', 'double'],
        'string': ['string', 'large_string', 'utf8'],
        'date': ['date32', 'date64'],
        'datetime': ['timestamp[ns]', 'timestamp[us]', 'timestamp[ms]'],
        'bool': ['bool'],
    }

    def __init__(self, catalog_path: Optional[str] = None):
        """
        Inicializa o validador de schema.

        Args:
            catalog_path: Caminho para catalog_focused.json (opcional)
        """
        if catalog_path is None:
            # Tentar localizar o catálogo em vários locais possíveis
            possible_paths = [
                Path(os.getcwd()) / "data" / "catalog_focused.json", # Root execution
                Path(os.getcwd()) / "backend" / "data" / "catalog_focused.json", # Outside backend
                Path(__file__).parent.parent.parent.parent.parent / "data" / "catalog_focused.json", # Relative to file
                Path(__file__).parent.parent.parent / "data" / "catalog_focused.json", # Old fallback
            ]
            
            for path in possible_paths:
                if path.exists():
                    catalog_path = path
                    break
            
            # Fallback se nenhum existir (vai falhar no load, mas pelo menos tentou)
            if catalog_path is None:
                catalog_path = possible_paths[0]

        self.catalog_path = Path(catalog_path)
        # self.catalog = self._load_catalog() # Adiar carregamento para evitar crash na init se arquivo não existir
        # Melhor: Tentar carregar, se falhar, logar warning e usar catalogo vazio
        try:
            self.catalog: Any = self._load_catalog()
        except FileNotFoundError:
            logger.warning(f"Catálogo não encontrado em {self.catalog_path}. Validação de schema será ignorada.")
            self.catalog = []

    def _load_catalog(self) -> Dict:
        """
        Carrega o catálogo de dados do arquivo JSON.

        Returns:
            Dict contendo o catálogo de dados

        Raises:
            FileNotFoundError: Se o catálogo não existir
            json.JSONDecodeError: Se o JSON for inválido
        """
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
            logger.info(f"Catálogo carregado: {self.catalog_path}")
            return catalog
        except FileNotFoundError:
            logger.error(f"Catálogo não encontrado: {self.catalog_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar catálogo JSON: {e}")
            raise

    def validate_parquet_file(self, parquet_path: str, table_name: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Valida um arquivo Parquet contra o catálogo.

        Args:
            parquet_path: Caminho para o arquivo Parquet
            table_name: Nome da tabela no catálogo (inferido do arquivo se None)

        Returns:
            Tupla (is_valid, errors) onde:
                - is_valid: True se schema válido
                - errors: Lista de mensagens de erro
        """
        errors = []

        try:
            # Carregar schema do Parquet
            parquet_file = pq.ParquetFile(parquet_path)
            parquet_schema = parquet_file.schema_arrow

            # Inferir nome da tabela se não fornecido
            if table_name is None:
                table_name = Path(parquet_path).stem

            # Buscar schema esperado no catálogo
            expected_schema = self._get_expected_schema(table_name)
            if expected_schema is None:
                errors.append(f"Tabela '{table_name}' não encontrada no catálogo")
                return False, errors

            # Validar colunas
            column_errors = self._validate_columns(parquet_schema, expected_schema, table_name)
            errors.extend(column_errors)

            # Validar tipos
            type_errors = self._validate_types(parquet_schema, expected_schema, table_name)
            errors.extend(type_errors)

            is_valid = len(errors) == 0

            if is_valid:
                logger.info(f"Schema válido para '{table_name}': {parquet_path}")
            else:
                logger.warning(f"Schema inválido para '{table_name}': {len(errors)} erros encontrados")

            return is_valid, errors

        except Exception as e:
            error_msg = f"Erro ao validar arquivo Parquet '{parquet_path}': {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            return False, errors

    def _get_expected_schema(self, table_name: str) -> Optional[Dict]:
        """
        Obtém o schema esperado do catálogo para uma tabela.

        Args:
            table_name: Nome da tabela

        Returns:
            Dict com schema esperado ou None se não encontrado
        """
        # Normalizar nome da tabela buscada
        search_name = table_name.lower().replace('_', '').replace('-', '')
        
        # Handle List structure (Current format of catalog_focused.json)
        if isinstance(self.catalog, list):
            for table_info in self.catalog:
                file_name = table_info.get("file_name", "")
                if not file_name:
                    continue
                    
                # Extrair nome base do arquivo (ex: "admatao.parquet" -> "admatao")
                catalog_table_name = Path(file_name).stem.lower().replace('_', '').replace('-', '')
                
                # Match exato
                if catalog_table_name == search_name:
                    return table_info
                
                # Match aproximado específico para admmat/admatao
                if (search_name == "admmat" and "admat" in catalog_table_name) or \
                   (search_name == "admatao" and "admmat" in catalog_table_name):
                    return table_info
                    
            return None

        # Handle Dict structure (Legacy format support)
        elif isinstance(self.catalog, dict):
            # Tentar encontrar a tabela no catálogo
            for table_key, table_info in self.catalog.items():
                # Normalizar nomes (remover prefixos, sufixos)
                normalized_key = table_key.lower().replace('_', '').replace('-', '')

                if normalized_key == search_name or table_key.lower() == table_name.lower():
                    return table_info

        return None

    def _validate_columns(self, parquet_schema: pa.Schema, expected_schema: Dict, table_name: str) -> List[str]:
        """
        Valida se as colunas esperadas estão presentes no Parquet.

        Args:
            parquet_schema: Schema do arquivo Parquet
            expected_schema: Schema esperado do catálogo
            table_name: Nome da tabela

        Returns:
            Lista de erros encontrados
        """
        errors = []

        # Obter colunas do Parquet
        parquet_columns = set(parquet_schema.names)

        # Obter colunas esperadas do catálogo
        expected_columns = set(expected_schema.get('columns', {}).keys())

        # Verificar colunas faltantes (esperadas mas não presentes)
        missing_columns = expected_columns - parquet_columns
        if missing_columns:
            errors.append(
                f"Tabela '{table_name}': Colunas faltantes: {sorted(missing_columns)}"
            )

        # Verificar colunas extras (presentes mas não esperadas) - apenas warning
        extra_columns = parquet_columns - expected_columns
        if extra_columns:
            logger.warning(
                f"Tabela '{table_name}': Colunas extras encontradas: {sorted(extra_columns)}"
            )

        return errors

    def _validate_types(self, parquet_schema: pa.Schema, expected_schema: Dict, table_name: str) -> List[str]:
        """
        Valida se os tipos de dados são compatíveis.

        Args:
            parquet_schema: Schema do arquivo Parquet
            expected_schema: Schema esperado do catálogo
            table_name: Nome da tabela

        Returns:
            Lista de erros de incompatibilidade de tipos
        """
        errors = []

        expected_columns = expected_schema.get('columns', {})

        for field in parquet_schema:
            column_name = field.name

            # Ignorar colunas não definidas no catálogo
            if column_name not in expected_columns:
                continue

            expected_type = expected_columns[column_name].get('type', 'string')
            parquet_type = str(field.type)

            # Verificar compatibilidade de tipos
            if not self._is_type_compatible(parquet_type, expected_type):
                errors.append(
                    f"Tabela '{table_name}', coluna '{column_name}': "
                    f"Tipo incompatível. Esperado: {expected_type}, "
                    f"Encontrado: {parquet_type}"
                )

        return errors

    def _is_type_compatible(self, parquet_type: str, expected_type: str) -> bool:
        """
        Verifica se um tipo Parquet é compatível com o tipo esperado.

        Args:
            parquet_type: Tipo do Parquet (ex: 'int64', 'string')
            expected_type: Tipo esperado do catálogo

        Returns:
            True se os tipos são compatíveis
        """
        # Normalizar tipos
        parquet_type_lower = parquet_type.lower()
        expected_type_lower = expected_type.lower()

        # Verificar igualdade direta
        if parquet_type_lower == expected_type_lower:
            return True

        # Verificar mapeamentos de tipos compatíveis
        for base_type, compatible_types in self.TYPE_MAPPING.items():
            if expected_type_lower in compatible_types or expected_type_lower == base_type:
                if parquet_type_lower in compatible_types or parquet_type_lower == base_type:
                    return True

        # Tipos numéricos são geralmente compatíveis entre si
        numeric_types = ['int', 'float', 'double', 'decimal']
        if any(nt in parquet_type_lower for nt in numeric_types) and \
           any(nt in expected_type_lower for nt in numeric_types):
            return True

        return False

    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        """
        Retorna o schema esperado para uma tabela do catálogo.

        Args:
            table_name: Nome da tabela

        Returns:
            Dict com schema da tabela ou None se não encontrada
        """
        return self._get_expected_schema(table_name)

    def list_required_columns(self, table_name: str) -> List[str]:
        """
        Lista as colunas obrigatórias de uma tabela.

        Args:
            table_name: Nome da tabela

        Returns:
            Lista de nomes de colunas obrigatórias
        """
        schema = self._get_expected_schema(table_name)
        if schema is None:
            return []

        return list(schema.get('columns', {}).keys())

    def validate_query_columns(self, table_name: str, query_columns: List[str]) -> Tuple[bool, List[str]]:
        """
        Valida se as colunas de uma query existem no schema.

        Args:
            table_name: Nome da tabela
            query_columns: Lista de colunas usadas na query

        Returns:
            Tupla (is_valid, invalid_columns)
        """
        schema = self._get_expected_schema(table_name)
        if schema is None:
            logger.warning(f"Tabela '{table_name}' não encontrada no catálogo")
            return True, []  # Assumir válido se tabela não está catalogada

        valid_columns = set(schema.get('columns', {}).keys())
        query_columns_set = set(query_columns)

        invalid_columns = query_columns_set - valid_columns

        is_valid = len(invalid_columns) == 0

        return is_valid, list(invalid_columns)


# Função auxiliar para validação rápida
def validate_parquet_schema(parquet_path: str, catalog_path: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Função auxiliar para validação rápida de schema Parquet.

    Args:
        parquet_path: Caminho para o arquivo Parquet
        catalog_path: Caminho para o catálogo (opcional)

    Returns:
        Tupla (is_valid, errors)
    """
    validator = SchemaValidator(catalog_path)
    return validator.validate_parquet_file(parquet_path)


if __name__ == "__main__":
    # Teste básico do validador
    logging.basicConfig(level=logging.INFO)

    # Exemplo de uso
    validator = SchemaValidator()

    # Validar arquivo de exemplo
    test_file = Path(__file__).parent.parent.parent / "data" / "parquet" / "produtos.parquet"
    if test_file.exists():
        is_valid, errors = validator.validate_parquet_file(str(test_file))
        print(f"\nValidação de {test_file.name}:")
        print(f"Válido: {is_valid}")
        if errors:
            print("Erros:")
            for error in errors:
                print(f"  - {error}")
    else:
        print(f"Arquivo de teste não encontrado: {test_file}")
