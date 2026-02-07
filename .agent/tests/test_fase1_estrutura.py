"""
FASE 1 — Testes de Validação de Estrutura

Este módulo contém testes automatizados que validam a existência
e integridade da estrutura do projeto Caculinha BI Agent Platform.

Uso:
    pytest tests/test_fase1_estrutura.py -v

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from pathlib import Path

import pytest


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

# Diretório base do projeto
# test_fase1_estrutura.py está em: BI_Solution/.agent/tests/
# Precisamos ir 2 níveis acima: tests -> .agent -> BI_Solution
BASE_DIR = Path(__file__).parent.parent.parent  # BI_Solution/
BACKEND_DIR = BASE_DIR / "backend"
AGENT_DIR = BASE_DIR / ".agent"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def base_path() -> Path:
    """Retorna o caminho base do projeto."""
    return BASE_DIR


@pytest.fixture
def backend_path() -> Path:
    """Retorna o caminho do backend."""
    return BACKEND_DIR


@pytest.fixture
def agent_path() -> Path:
    """Retorna o caminho do Antigravity Kit."""
    return AGENT_DIR


# =============================================================================
# TESTES DE EXISTÊNCIA — DIRETÓRIOS PRINCIPAIS
# =============================================================================

class TestDiretoriosPrincipais:
    """Valida existência dos diretórios principais do projeto."""
    
    def test_backend_existe(self, backend_path: Path):
        """Backend directory deve existir."""
        assert backend_path.exists(), f"Backend não encontrado: {backend_path}"
        assert backend_path.is_dir(), f"Backend não é diretório: {backend_path}"
    
    def test_agent_existe(self, agent_path: Path):
        """Antigravity Kit directory deve existir."""
        assert agent_path.exists(), f".agent não encontrado: {agent_path}"
        assert agent_path.is_dir(), f".agent não é diretório: {agent_path}"
    
    def test_backend_app_existe(self, backend_path: Path):
        """Backend/app directory deve existir."""
        app_path = backend_path / "app"
        assert app_path.exists(), f"app/ não encontrado: {app_path}"
    
    def test_backend_data_existe(self, backend_path: Path):
        """Backend/data directory deve existir."""
        data_path = backend_path / "data"
        assert data_path.exists(), f"data/ não encontrado: {data_path}"


# =============================================================================
# TESTES DE EXISTÊNCIA — ESTRUTURA APP
# =============================================================================

class TestEstruturaApp:
    """Valida estrutura interna de backend/app."""
    
    SUBDIRS_OBRIGATORIOS = [
        "api",
        "core",
        "infrastructure",
        "services",
        "schemas",
    ]
    
    @pytest.mark.parametrize("subdir", SUBDIRS_OBRIGATORIOS)
    def test_subdiretorio_existe(self, backend_path: Path, subdir: str):
        """Subdiretórios obrigatórios devem existir."""
        path = backend_path / "app" / subdir
        assert path.exists(), f"Subdiretório não encontrado: {path}"
        assert path.is_dir(), f"Não é diretório: {path}"


# =============================================================================
# TESTES DE EXISTÊNCIA — ARQUIVOS CRÍTICOS
# =============================================================================

class TestArquivosCriticos:
    """Valida existência de arquivos críticos."""
    
    def test_main_py_existe(self, backend_path: Path):
        """main.py deve existir."""
        main_py = backend_path / "main.py"
        assert main_py.exists(), f"main.py não encontrado: {main_py}"
    
    def test_requirements_existe(self, backend_path: Path):
        """requirements.txt deve existir."""
        req = backend_path / "requirements.txt"
        assert req.exists(), f"requirements.txt não encontrado: {req}"
    
    def test_env_example_existe(self, backend_path: Path):
        """Arquivo .env.example deve existir."""
        env_example = backend_path / ".env.example"
        assert env_example.exists(), f".env.example não encontrado: {env_example}"


# =============================================================================
# TESTES DE EXISTÊNCIA — AGENTES
# =============================================================================

class TestAgentes:
    """Valida existência dos agentes de IA."""
    
    def test_agents_dir_existe(self, backend_path: Path):
        """Diretório de agentes deve existir."""
        agents_dir = backend_path / "app" / "core" / "agents"
        assert agents_dir.exists(), f"Diretório agents não encontrado: {agents_dir}"
    
    def test_caculinha_agent_existe(self, backend_path: Path):
        """CaculinhaBIAgent deve existir."""
        agent = backend_path / "app" / "core" / "agents" / "caculinha_bi_agent.py"
        assert agent.exists(), f"CaculinhaBIAgent não encontrado: {agent}"
    
    def test_base_agent_existe(self, backend_path: Path):
        """BaseAgent deve existir."""
        agent = backend_path / "app" / "core" / "agents" / "base_agent.py"
        assert agent.exists(), f"BaseAgent não encontrado: {agent}"


# =============================================================================
# TESTES DE EXISTÊNCIA — FERRAMENTAS
# =============================================================================

class TestFerramentas:
    """Valida existência das ferramentas de BI."""
    
    FERRAMENTAS_OBRIGATORIAS = [
        "chart_tools.py",
        "une_tools.py",
        "flexible_query_tool.py",
        "advanced_analytics_tool.py",
        "metadata_tools.py",
    ]
    
    def test_tools_dir_existe(self, backend_path: Path):
        """Diretório de ferramentas deve existir."""
        tools_dir = backend_path / "app" / "core" / "tools"
        assert tools_dir.exists(), f"Diretório tools não encontrado: {tools_dir}"
    
    @pytest.mark.parametrize("ferramenta", FERRAMENTAS_OBRIGATORIAS)
    def test_ferramenta_existe(self, backend_path: Path, ferramenta: str):
        """Ferramenta obrigatória deve existir."""
        tool_path = backend_path / "app" / "core" / "tools" / ferramenta
        assert tool_path.exists(), f"Ferramenta não encontrada: {tool_path}"


# =============================================================================
# TESTES DE EXISTÊNCIA — ENDPOINTS
# =============================================================================

class TestEndpoints:
    """Valida existência dos endpoints da API."""
    
    ENDPOINTS_OBRIGATORIOS = [
        "chat.py",
        "dashboard.py",
        "auth.py",
        "metrics.py",
        "insights.py",
    ]
    
    def test_endpoints_dir_existe(self, backend_path: Path):
        """Diretório de endpoints deve existir."""
        endpoints_dir = backend_path / "app" / "api" / "v1" / "endpoints"
        assert endpoints_dir.exists(), f"Diretório endpoints não encontrado: {endpoints_dir}"
    
    @pytest.mark.parametrize("endpoint", ENDPOINTS_OBRIGATORIOS)
    def test_endpoint_existe(self, backend_path: Path, endpoint: str):
        """Endpoint obrigatório deve existir."""
        endpoint_path = backend_path / "app" / "api" / "v1" / "endpoints" / endpoint
        assert endpoint_path.exists(), f"Endpoint não encontrado: {endpoint_path}"


# =============================================================================
# TESTES DE EXISTÊNCIA — ANTIGRAVITY KIT
# =============================================================================

class TestAntigravityKit:
    """Valida estrutura do Antigravity Kit."""
    
    SUBDIRS_ANTIGRAVITY = [
        "agents",
        "skills",
        "workflows",
    ]
    
    @pytest.mark.parametrize("subdir", SUBDIRS_ANTIGRAVITY)
    def test_antigravity_subdir_existe(self, agent_path: Path, subdir: str):
        """Subdiretórios do Antigravity Kit devem existir."""
        path = agent_path / subdir
        assert path.exists(), f"Antigravity subdir não encontrado: {path}"
    
    def test_architecture_md_existe(self, agent_path: Path):
        """ARCHITECTURE.md deve existir."""
        arch = agent_path / "ARCHITECTURE.md"
        assert arch.exists(), f"ARCHITECTURE.md não encontrado: {arch}"


# =============================================================================
# TESTES DE EXISTÊNCIA — DOCUMENTAÇÃO FASE 1
# =============================================================================

class TestDocumentacaoFase1:
    """Valida existência da documentação gerada na FASE 1."""
    
    DOCS_OBRIGATORIOS = [
        "diagnostico.md",
        "riscos.md",
        "mapa_modulos.md",
    ]
    
    def test_docs_dir_existe(self, agent_path: Path):
        """Diretório docs deve existir."""
        docs_dir = agent_path / "docs"
        assert docs_dir.exists(), f"Diretório docs não encontrado: {docs_dir}"
    
    @pytest.mark.parametrize("doc", DOCS_OBRIGATORIOS)
    def test_doc_existe(self, agent_path: Path, doc: str):
        """Documento obrigatório da FASE 1 deve existir."""
        doc_path = agent_path / "docs" / doc
        assert doc_path.exists(), f"Documento não encontrado: {doc_path}"
    
    @pytest.mark.parametrize("doc", DOCS_OBRIGATORIOS)
    def test_doc_nao_vazio(self, agent_path: Path, doc: str):
        """Documento da FASE 1 não deve estar vazio."""
        doc_path = agent_path / "docs" / doc
        if doc_path.exists():
            content = doc_path.read_text(encoding="utf-8")
            assert len(content) > 100, f"Documento muito curto: {doc_path}"


# =============================================================================
# TESTES DE CONTAGEM — MÉTRICAS
# =============================================================================

class TestMetricasEstrutura:
    """Valida métricas mínimas da estrutura."""
    
    def test_minimo_endpoints(self, backend_path: Path):
        """Deve haver pelo menos 10 endpoints."""
        endpoints_dir = backend_path / "app" / "api" / "v1" / "endpoints"
        if endpoints_dir.exists():
            count = len([f for f in endpoints_dir.iterdir() if f.suffix == ".py"])
            assert count >= 10, f"Poucos endpoints: {count}"
    
    def test_minimo_ferramentas(self, backend_path: Path):
        """Deve haver pelo menos 10 ferramentas."""
        tools_dir = backend_path / "app" / "core" / "tools"
        if tools_dir.exists():
            count = len([f for f in tools_dir.iterdir() if f.suffix == ".py"])
            assert count >= 10, f"Poucas ferramentas: {count}"
    
    def test_minimo_agentes_antigravity(self, agent_path: Path):
        """Deve haver pelo menos 10 agentes Antigravity."""
        agents_dir = agent_path / "agents"
        if agents_dir.exists():
            count = len([f for f in agents_dir.iterdir() if f.suffix == ".md"])
            assert count >= 10, f"Poucos agentes Antigravity: {count}"


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
