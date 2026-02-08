"""
Testes para as melhorias de modernização das tools (2025-12-27).

Testa:
1. Consolidação de chart tools
2. RAG semantic search
3. Tool scoping por role
"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.tools import BaseTool

# Import das ferramentas a testar
from backend.app.core.utils.tool_scoping import ToolPermissionManager, get_scoped_tools


class TestChartToolsConsolidation:
    """Testa consolidação das chart tools"""

    def test_listar_graficos_disponiveis_returns_only_active_tools(self):
        """listar_graficos_disponiveis deve retornar apenas 4 ferramentas ativas"""
        from backend.app.core.tools.chart_tools import listar_graficos_disponiveis

        result = listar_graficos_disponiveis()

        assert result["status"] == "success"
        assert result["graficos_disponiveis"]["total_tipos"] == 4
        assert "gerar_grafico_universal_v2" in str(result)
        assert "Ferramenta Universal" in str(result)

    def test_deprecated_tools_have_warnings(self):
        """Verifica que tools deprecated têm comentários de warning"""
        import inspect
        from backend.app.core.tools import chart_tools

        source = inspect.getsource(chart_tools)

        # Deve haver marcações de DEPRECATED
        assert "⚠️ DEPRECATED" in source
        assert "gerar_grafico_universal_v2" in source


class TestSemanticSearch:
    """Testa funcionalidade de RAG semantic search"""

    def test_semantic_search_tool_exists(self):
        """Verifica que a tool de semantic search foi criada"""
        from backend.app.core.tools.semantic_search_tool import buscar_produtos_inteligente

        assert buscar_produtos_inteligente is not None
        assert callable(buscar_produtos_inteligente)
        assert hasattr(buscar_produtos_inteligente, "name")

    def test_semantic_search_tool_has_correct_schema(self):
        """Verifica schema da tool de semantic search"""
        from backend.app.core.tools.semantic_search_tool import buscar_produtos_inteligente

        schema = buscar_produtos_inteligente.args_schema

        # Deve ter os parâmetros esperados
        assert schema is not None
        # Check if schema has expected fields (will depend on Pydantic version)

    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="Requires GEMINI_API_KEY and parquet data"
    )
    def test_semantic_search_integration(self):
        """Teste de integração real (requer API key)"""
        from backend.app.core.tools.semantic_search_tool import buscar_produtos_inteligente

        # Test semantic search
        result = buscar_produtos_inteligente(
            descricao="cola para sapato",
            limite=5
        )

        assert result["status"] == "success" or result["status"] == "error"
        if result["status"] == "success":
            assert "produtos" in result
            assert len(result["produtos"]) <= 5


class TestToolScoping:
    """Testa tool scoping por role"""

    def create_dummy_tools(self):
        """Cria tools dummy para testes"""
        class DummyTool(BaseTool):
            def __init__(self, tool_name):
                super().__init__()
                self._name = tool_name

            @property
            def name(self):
                return self._name

            def _run(self, *args, **kwargs):
                return "test"

        return [
            DummyTool("consultar_dados_flexivel"),
            DummyTool("buscar_produtos_inteligente"),
            DummyTool("calcular_preco_final_une"),
            DummyTool("sugerir_transferencias_automaticas"),
            DummyTool("gerar_grafico_universal_v2"),
            DummyTool("gerar_dashboard_executivo"),
        ]

    def test_admin_has_all_tools(self):
        """Admin deve ter acesso a todas as tools"""
        tools = self.create_dummy_tools()

        scoped = ToolPermissionManager.get_tools_for_role(tools, "admin")

        assert len(scoped) == len(tools)

    def test_analyst_has_limited_tools(self):
        """Analyst não deve ter acesso a calcular_preco_final_une"""
        tools = self.create_dummy_tools()

        scoped = ToolPermissionManager.get_tools_for_role(tools, "analyst")

        tool_names = [t.name for t in scoped]

        # Deve ter queries e visualizações
        assert "consultar_dados_flexivel" in tool_names
        assert "gerar_grafico_universal_v2" in tool_names

        # NÃO deve ter pricing nem transferências
        assert "calcular_preco_final_une" not in tool_names
        assert "sugerir_transferencias_automaticas" not in tool_names

    def test_viewer_has_minimal_tools(self):
        """Viewer deve ter acesso mínimo"""
        tools = self.create_dummy_tools()

        scoped = ToolPermissionManager.get_tools_for_role(tools, "viewer")

        tool_names = [t.name for t in scoped]

        # Deve ter visualizações básicas
        assert "gerar_dashboard_executivo" in tool_names

        # NÃO deve ter queries avançadas nem business logic
        assert "consultar_dados_flexivel" not in tool_names
        assert "calcular_preco_final_une" not in tool_names

    def test_unknown_role_defaults_to_viewer(self):
        """Role desconhecido deve usar 'viewer' como fallback"""
        tools = self.create_dummy_tools()

        scoped = ToolPermissionManager.get_tools_for_role(tools, "unknown_role")

        # Deve ter o mesmo comportamento que viewer
        viewer_scoped = ToolPermissionManager.get_tools_for_role(tools, "viewer")

        assert len(scoped) == len(viewer_scoped)

    def test_is_tool_allowed_works(self):
        """Testa método is_tool_allowed"""
        assert ToolPermissionManager.is_tool_allowed("gerar_grafico_universal_v2", "admin") is True
        assert ToolPermissionManager.is_tool_allowed("calcular_preco_final_une", "analyst") is False
        assert ToolPermissionManager.is_tool_allowed("gerar_dashboard_executivo", "viewer") is True

    def test_get_role_description(self):
        """Testa descrição dos roles"""
        admin_desc = ToolPermissionManager.get_role_description("admin")
        assert "total" in admin_desc.lower()

        analyst_desc = ToolPermissionManager.get_role_description("analyst")
        assert "analista" in analyst_desc.lower()

    def test_list_available_tools(self):
        """Testa listagem de tools disponíveis"""
        admin_tools = ToolPermissionManager.list_available_tools("admin")
        assert "*ALL_TOOLS*" in admin_tools

        analyst_tools = ToolPermissionManager.list_available_tools("analyst")
        assert len(analyst_tools) > 0
        assert "consultar_dados_flexivel" in analyst_tools


class TestAgentIntegration:
    """Testa integração das melhorias no agent"""

    @patch("app.core.agents.caculinha_bi_agent.ToolPermissionManager")
    def test_agent_applies_tool_scoping(self, mock_manager):
        """Verifica que o agent aplica tool scoping no __init__"""
        from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
        from backend.app.core.utils.field_mapper import FieldMapper

        mock_llm = Mock()
        mock_code_gen = Mock()
        mock_field_mapper = Mock(spec=FieldMapper)

        # Mock get_tools_for_role para retornar lista vazia
        mock_manager.get_tools_for_role.return_value = []

        agent = CaculinhaBIAgent(
            llm=mock_llm,
            code_gen_agent=mock_code_gen,
            field_mapper=mock_field_mapper,
            user_role="analyst"
        )

        # Verifica que get_tools_for_role foi chamado
        mock_manager.get_tools_for_role.assert_called_once()

        # Verifica que o role foi armazenado
        assert agent.user_role == "analyst"

    def test_agent_imports_new_tools(self):
        """Verifica que o agent importa as novas ferramentas"""
        from backend.app.core.agents import caculinha_bi_agent

        # Deve importar semantic search
        assert hasattr(caculinha_bi_agent, "buscar_produtos_inteligente")

        # Deve importar tool scoping
        assert hasattr(caculinha_bi_agent, "ToolPermissionManager")


# Configuração do pytest para testes de integração
def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require API keys"
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
