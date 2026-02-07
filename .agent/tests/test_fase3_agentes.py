"""
FASE 3 — Testes de Validação dos Agentes

Este módulo contém testes automatizados que validam a existência
e estrutura dos agentes criados na FASE 3.

Uso:
    pytest tests/test_fase3_agentes.py -v

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from pathlib import Path

import pytest


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

BASE_DIR = Path(__file__).parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
APPLICATION_DIR = BACKEND_DIR / "application"
AGENTS_DIR = APPLICATION_DIR / "agents"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def agents_path() -> Path:
    return AGENTS_DIR


# =============================================================================
# TESTES — APPLICATION LAYER
# =============================================================================

class TestApplicationLayerExiste:
    """Valida existência da Application Layer."""
    
    def test_application_dir_existe(self):
        assert APPLICATION_DIR.exists(), f"Application não encontrado: {APPLICATION_DIR}"
    
    def test_agents_dir_existe(self, agents_path: Path):
        assert agents_path.exists(), f"Agents não encontrado: {agents_path}"


# =============================================================================
# TESTES — AGENTES
# =============================================================================

class TestAgentes:
    """Valida existência de todos os agentes."""
    
    AGENTES_OBRIGATORIOS = [
        "base_agent.py",
        "orchestrator_agent.py",
        "sql_agent.py",
        "insight_agent.py",
        "forecast_agent.py",
        "metadata_agent.py",
        "tenant_agent.py",
        "security_agent.py",
        "monitoring_agent.py",
    ]
    
    @pytest.mark.parametrize("agente", AGENTES_OBRIGATORIOS)
    def test_agente_existe(self, agents_path: Path, agente: str):
        """Agente obrigatório deve existir."""
        agent_path = agents_path / agente
        assert agent_path.exists(), f"Agente não encontrado: {agent_path}"
    
    @pytest.mark.parametrize("agente", AGENTES_OBRIGATORIOS)
    def test_agente_nao_vazio(self, agents_path: Path, agente: str):
        """Agente não deve estar vazio."""
        agent_path = agents_path / agente
        if agent_path.exists():
            content = agent_path.read_text(encoding="utf-8")
            assert len(content) > 500, f"Agente muito curto: {agent_path}"
    
    @pytest.mark.parametrize("agente", AGENTES_OBRIGATORIOS[1:])  # Excluir base_agent
    def test_agente_herda_base(self, agents_path: Path, agente: str):
        """Agentes devem herdar de BaseAgent."""
        agent_path = agents_path / agente
        if agent_path.exists():
            content = agent_path.read_text(encoding="utf-8")
            assert "BaseAgent" in content, f"Agente não herda BaseAgent: {agent_path}"


# =============================================================================
# TESTES — ESTRUTURA DOS AGENTES
# =============================================================================

class TestEstruturaAgentes:
    """Valida estrutura interna dos agentes."""
    
    AGENTES_ESPECIALIZADOS = [
        "orchestrator_agent.py",
        "sql_agent.py",
        "insight_agent.py",
        "forecast_agent.py",
        "metadata_agent.py",
        "tenant_agent.py",
        "security_agent.py",
        "monitoring_agent.py",
    ]
    
    @pytest.mark.parametrize("agente", AGENTES_ESPECIALIZADOS)
    def test_agente_tem_name_property(self, agents_path: Path, agente: str):
        """Agente deve ter property 'name'."""
        agent_path = agents_path / agente
        if agent_path.exists():
            content = agent_path.read_text(encoding="utf-8")
            assert "def name(self)" in content, f"Agente sem name: {agent_path}"
    
    @pytest.mark.parametrize("agente", AGENTES_ESPECIALIZADOS)
    def test_agente_tem_description_property(self, agents_path: Path, agente: str):
        """Agente deve ter property 'description'."""
        agent_path = agents_path / agente
        if agent_path.exists():
            content = agent_path.read_text(encoding="utf-8")
            assert "def description(self)" in content, f"Agente sem description: {agent_path}"
    
    @pytest.mark.parametrize("agente", AGENTES_ESPECIALIZADOS)
    def test_agente_tem_capabilities_property(self, agents_path: Path, agente: str):
        """Agente deve ter property 'capabilities'."""
        agent_path = agents_path / agente
        if agent_path.exists():
            content = agent_path.read_text(encoding="utf-8")
            assert "def capabilities(self)" in content, f"Agente sem capabilities: {agent_path}"
    
    @pytest.mark.parametrize("agente", AGENTES_ESPECIALIZADOS)
    def test_agente_tem_execute(self, agents_path: Path, agente: str):
        """Agente deve ter método _execute."""
        agent_path = agents_path / agente
        if agent_path.exists():
            content = agent_path.read_text(encoding="utf-8")
            assert "async def _execute" in content, f"Agente sem _execute: {agent_path}"
    
    @pytest.mark.parametrize("agente", AGENTES_ESPECIALIZADOS)
    def test_agente_tem_get_tools(self, agents_path: Path, agente: str):
        """Agente deve ter método get_tools."""
        agent_path = agents_path / agente
        if agent_path.exists():
            content = agent_path.read_text(encoding="utf-8")
            assert "def get_tools(self)" in content, f"Agente sem get_tools: {agent_path}"


# =============================================================================
# TESTES — CONTAGEM
# =============================================================================

class TestMetricasAgentes:
    """Valida métricas mínimas dos agentes."""
    
    def test_minimo_agentes(self, agents_path: Path):
        """Deve haver pelo menos 9 arquivos de agente."""
        if agents_path.exists():
            count = len([f for f in agents_path.iterdir() if f.suffix == ".py"])
            assert count >= 9, f"Poucos agentes: {count}"
    
    def test_init_exporta_agentes(self, agents_path: Path):
        """__init__.py deve exportar todos os agentes."""
        init_path = agents_path / "__init__.py"
        if init_path.exists():
            content = init_path.read_text(encoding="utf-8")
            agentes = ["OrchestratorAgent", "SQLAgent", "InsightAgent", 
                       "ForecastAgent", "MetadataAgent", "TenantAgent",
                       "SecurityAgent", "MonitoringAgent"]
            for agente in agentes:
                assert agente in content, f"__init__.py não exporta {agente}"


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
