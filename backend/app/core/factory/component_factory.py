"""
Fábrica de Componentes

Este módulo implementa o padrão Factory para criar e gerenciar instâncias
dos diversos componentes do sistema, facilitando a integração entre eles
e reduzindo o acoplamento.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ComponentFactory:
    """Fábrica para criar e gerenciar componentes do sistema"""

    # Dicionário para armazenar as instâncias dos componentes (Singleton)
    _components: Dict[str, Any] = {}

    @classmethod
    def get_data_adapter(cls):
        """Obtém uma instância do adaptador de dados DuckDB Enhanced"""
        if "data_adapter" not in cls._components:
            from app.infrastructure.data.duckdb_enhanced_adapter import get_duckdb_adapter
            logger.info("Obtendo instância do DuckDBEnhancedAdapter")
            cls._components["data_adapter"] = get_duckdb_adapter()
        return cls._components["data_adapter"]

    @classmethod
    def reset_component(cls, component_name: str) -> bool:
        """Reinicia um componente específico, removendo sua instância atual

        Args:
            component_name (str): Nome do componente a ser reiniciado

        Returns:
            bool: True se o componente foi reiniciado com sucesso, False caso contrário
        """
        if component_name in cls._components:
            del cls._components[component_name]
            logger.info(f"Componente reiniciado: {component_name}")
            return True

        logger.warning(
            f"Tentativa de reiniciar componente inexistente: {component_name}"
        )
        return False

    @classmethod
    def reset_all(cls) -> None:
        """Reinicia todos os componentes, removendo todas as instâncias atuais"""
        cls._components.clear()
        logger.info("Todos os componentes foram reiniciados")
