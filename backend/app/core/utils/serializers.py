"""
Utilit\u00e1rios de serializa\u00e7\u00e3o para tipos complexos Python/SQLAlchemy.
Resolve erros como "Object of type MapComposite is not JSON serializable".
"""
import json
import logging
from typing import Any, Dict, List
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TypeConverter:
    """Conversor gen\u00e9rico de tipos para serializa\u00e7\u00e3o JSON."""

    @staticmethod
    def convert(obj: Any) -> Any:
        """
        Converte qualquer objeto para formato JSON-serializ\u00e1vel.

        Trata casos especiais:
        - SQLAlchemy Row / MapComposite
        - Tipos numpy (int64, float64, etc.)
        - Tipos pandas (Timestamp, Timedelta)
        - Datetime, Decimal, bytes
        - Objetos gen\u00e9ricos com __dict__

        Args:
            obj: Objeto a ser convertido

        Returns:
            Objeto serializ\u00e1vel em JSON
        """

        # SQLAlchemy Row / MapComposite - CRIT\u00cdCO para resolver o erro
        if hasattr(obj, '_mapping'):
            return dict(obj._mapping)

        # Listas e tuplas
        if isinstance(obj, (list, tuple)):
            return [TypeConverter.convert(item) for item in obj]

        # Dicion\u00e1rios
        if isinstance(obj, dict):
            return {k: TypeConverter.convert(v) for k, v in obj.items()}

        # Tipos primitivos j\u00e1 serializ\u00e1veis
        if isinstance(obj, (int, float, bool, str, type(None))):
            return obj

        # Tipos numpy
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            val = float(obj)
            return None if (np.isnan(val) or np.isinf(val)) else val
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)

        # Tipos pandas
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, pd.Timedelta):
            return str(obj)
        if pd.isna(obj):
            return None

        # Tipos datetime
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        # Decimal
        if isinstance(obj, Decimal):
            return float(obj)

        # Bytes
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')

        # Sets
        if isinstance(obj, set):
            return list(obj)

        # Objetos gen\u00e9ricos com __dict__
        if hasattr(obj, '__dict__') and not isinstance(obj, type):
            return {k: TypeConverter.convert(v)
                   for k, v in obj.__dict__.items()
                   if not k.startswith('_')}

        # \u00daltimo recurso: converter para string
        logger.warning(f"Tipo desconhecido {type(obj)}: {obj}, convertendo para string")
        return str(obj)

    @staticmethod
    def to_json(obj: Any, **kwargs) -> str:
        """
        Converte objeto para string JSON de forma segura.

        Args:
            obj: Objeto a ser convertido
            **kwargs: Argumentos adicionais para json.dumps

        Returns:
            String JSON
        """
        try:
            converted = TypeConverter.convert(obj)
            if 'ensure_ascii' not in kwargs:
                kwargs['ensure_ascii'] = False
            return json.dumps(converted, **kwargs)
        except Exception as e:
            logger.error(f"Falha na convers\u00e3o JSON: {e}", exc_info=True)
            return json.dumps({"error": f"Serializa\u00e7\u00e3o falhou: {str(e)}"}, ensure_ascii=False)

    @staticmethod
    def from_query_rows(rows: List[Any]) -> List[Dict[str, Any]]:
        """
        Converte linhas de resultado de query para lista de dicion\u00e1rios.
        Especialmente \u00fatil para resultados SQLAlchemy.

        Args:
            rows: Lista de Row objects ou dicts

        Returns:
            Lista de dicion\u00e1rios JSON-serializ\u00e1veis
        """
        results = []
        for row in rows:
            if hasattr(row, '_mapping'):
                # SQLAlchemy Row com _mapping
                results.append(TypeConverter.convert(dict(row._mapping)))
            elif isinstance(row, dict):
                # J\u00e1 \u00e9 dict, mas pode conter tipos n\u00e3o-serializ\u00e1veis
                results.append(TypeConverter.convert(row))
            else:
                # Tentar converter diretamente
                results.append(TypeConverter.convert(row))

        return results


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    Wrapper para TypeConverter.to_json() para compatibilidade com c\u00f3digo existente.

    Args:
        obj: Objeto a ser convertido
        **kwargs: Argumentos para json.dumps

    Returns:
        String JSON
    """
    return TypeConverter.to_json(obj, **kwargs)


def convert_mapcomposite(obj: Any) -> Any:
    """
    Converte recursivamente objetos MapComposite para dict.
    Fun\u00e7\u00e3o auxiliar para compatibilidade com c\u00f3digo existente.

    Args:
        obj: Objeto a ser convertido

    Returns:
        Objeto com MapComposite convertido
    """
    if hasattr(obj, '_mapping'):
        return dict(obj._mapping)
    elif isinstance(obj, dict):
        return {k: convert_mapcomposite(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_mapcomposite(item) for item in obj]
    return obj
