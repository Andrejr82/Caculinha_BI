"""
Tool Scoping - Controle de acesso a ferramentas baseado em role do usuário.

Implementa permission boundaries para agents, limitando quais ferramentas
cada tipo de usuário pode acessar (security best practice 2025).

Author: Context7 2025
"""

import logging
from typing import List, Optional
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class ToolPermissionManager:
    """Gerencia permissões de ferramentas por role de usuário"""

    # Define quais tools cada role pode acessar
    ROLE_PERMISSIONS = {
        "admin": {
            "description": "Acesso total a todas as ferramentas",
            "allowed_tools": "*",  # Todas as tools
            "denied_tools": []
        },
        "analyst": {
            "description": "Analista de dados - acesso a queries e visualizações",
            "allowed_tools": [
                # Data Query
                "consultar_dados_flexivel",
                "buscar_produtos_inteligente",
                "consultar_dados_gerais",
                # Business Logic (read-only)
                "calcular_abastecimento_une",
                "calcular_mc_produto",
                "encontrar_rupturas_criticas",
                # Visualizations
                "gerar_grafico_universal_v2",
                "gerar_ranking_produtos_mais_vendidos",
                "gerar_dashboard_executivo",
                "listar_graficos_disponiveis",
                "gerar_visualizacao_customizada",
            ],
            "denied_tools": [
                # Não pode calcular preços nem sugerir transferências
                "calcular_preco_final_une",
                "validar_transferencia_produto",
                "sugerir_transferencias_automaticas"
            ]
        },
        "viewer": {
            "description": "Visualizador - acesso somente leitura",
            "allowed_tools": [
                # Queries básicas
                "consultar_dados_gerais",
                "buscar_produtos_inteligente",
                # Visualizações apenas
                "gerar_grafico_universal_v2",
                "gerar_dashboard_executivo",
                "listar_graficos_disponiveis",
            ],
            "denied_tools": [
                # Não pode acessar business logic
                "calcular_abastecimento_une",
                "calcular_mc_produto",
                "calcular_preco_final_une",
                "validar_transferencia_produto",
                "sugerir_transferencias_automaticas",
                "encontrar_rupturas_criticas",
                # Nem queries avançadas
                "consultar_dados_flexivel",
            ]
        },
        "guest": {
            "description": "Convidado - acesso mínimo",
            "allowed_tools": [
                "listar_graficos_disponiveis",
                "gerar_dashboard_executivo"
            ],
            "denied_tools": "*"
        }
    }

    @classmethod
    def get_tools_for_role(
        cls,
        all_tools: List[BaseTool],
        user_role: str = "viewer"
    ) -> List[BaseTool]:
        """
        Retorna lista de ferramentas filtrada baseada no role do usuário.

        Args:
            all_tools: Lista completa de ferramentas disponíveis
            user_role: Role do usuário (admin, analyst, viewer, guest)

        Returns:
            Lista filtrada de ferramentas que o usuário pode acessar
        """
        # Normalizar role
        user_role = user_role.lower()

        if user_role not in cls.ROLE_PERMISSIONS:
            logger.warning(
                f"Role '{user_role}' não reconhecido. Usando 'viewer' como fallback."
            )
            user_role = "viewer"

        permissions = cls.ROLE_PERMISSIONS[user_role]

        # Admin tem acesso a tudo
        if permissions["allowed_tools"] == "*":
            logger.info(f"User role '{user_role}' has access to all {len(all_tools)} tools")
            return all_tools

        # Filtrar tools baseado na whitelist
        allowed_tool_names = set(permissions["allowed_tools"])
        filtered_tools = [
            tool for tool in all_tools
            if tool.name in allowed_tool_names
        ]

        logger.info(
            f"User role '{user_role}' has access to {len(filtered_tools)}/{len(all_tools)} tools"
        )
        logger.debug(f"Allowed tools: {[t.name for t in filtered_tools]}")

        return filtered_tools

    @classmethod
    def is_tool_allowed(cls, tool_name: str, user_role: str = "viewer") -> bool:
        """
        Verifica se uma ferramenta específica é permitida para um role.

        Args:
            tool_name: Nome da ferramenta
            user_role: Role do usuário

        Returns:
            True se permitido, False caso contrário
        """
        user_role = user_role.lower()

        if user_role not in cls.ROLE_PERMISSIONS:
            user_role = "viewer"

        permissions = cls.ROLE_PERMISSIONS[user_role]

        # Admin pode tudo
        if permissions["allowed_tools"] == "*":
            return True

        # Verificar whitelist
        return tool_name in permissions["allowed_tools"]

    @classmethod
    def get_role_description(cls, user_role: str) -> str:
        """Retorna descrição do nível de acesso do role"""
        user_role = user_role.lower()

        if user_role in cls.ROLE_PERMISSIONS:
            return cls.ROLE_PERMISSIONS[user_role]["description"]
        return "Role não reconhecido"

    @classmethod
    def list_available_tools(cls, user_role: str = "viewer") -> List[str]:
        """
        Lista nomes das ferramentas disponíveis para um role.

        Args:
            user_role: Role do usuário

        Returns:
            Lista de nomes de ferramentas permitidas
        """
        user_role = user_role.lower()

        if user_role not in cls.ROLE_PERMISSIONS:
            user_role = "viewer"

        permissions = cls.ROLE_PERMISSIONS[user_role]

        if permissions["allowed_tools"] == "*":
            return ["*ALL_TOOLS*"]

        return permissions["allowed_tools"]


# Função helper para uso direto no agent
def get_scoped_tools(
    all_tools: List[BaseTool],
    user_data: Optional[dict] = None
) -> List[BaseTool]:
    """
    Helper function para obter tools filtradas baseado no user data.

    Args:
        all_tools: Lista de todas as ferramentas
        user_data: Dicionário com dados do usuário (deve conter 'role')

    Returns:
        Lista filtrada de ferramentas

    Example:
        >>> user = {"username": "john", "role": "analyst"}
        >>> scoped_tools = get_scoped_tools(bi_tools, user)
    """
    if not user_data:
        logger.warning("No user data provided, defaulting to 'viewer' role")
        user_role = "viewer"
    else:
        user_role = user_data.get("role", "viewer")

    return ToolPermissionManager.get_tools_for_role(all_tools, user_role)


# Exemplo de uso em log
if __name__ == "__main__":
    # Simulação de ferramentas
    class DummyTool:
        def __init__(self, name):
            self.name = name

    tools = [
        DummyTool("consultar_dados_flexivel"),
        DummyTool("calcular_preco_final_une"),
        DummyTool("gerar_grafico_universal_v2"),
    ]

    print("=== TOOL SCOPING EXAMPLES ===\n")

    for role in ["admin", "analyst", "viewer", "guest"]:
        scoped = ToolPermissionManager.get_tools_for_role(tools, role)
        print(f"{role.upper()}: {len(scoped)} tools")
        print(f"  → {[t.name for t in scoped]}\n")
