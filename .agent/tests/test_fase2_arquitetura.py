"""
FASE 2 — Testes de Validação de Arquitetura

Este módulo contém testes automatizados que validam a nova estrutura
Clean Architecture criada na FASE 2.

Uso:
    pytest tests/test_fase2_arquitetura.py -v

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
# test_fase2_arquitetura.py está em: BI_Solution/.agent/tests/
# Precisamos ir 2 níveis acima: tests -> .agent -> BI_Solution
BASE_DIR = Path(__file__).parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DOMAIN_DIR = BACKEND_DIR / "domain"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def domain_path() -> Path:
    """Retorna o caminho do Domain Layer."""
    return DOMAIN_DIR


@pytest.fixture
def backend_path() -> Path:
    """Retorna o caminho do backend."""
    return BACKEND_DIR


# =============================================================================
# TESTES — DOMAIN LAYER EXISTÊNCIA
# =============================================================================

class TestDomainLayerExiste:
    """Valida existência do Domain Layer."""
    
    def test_domain_dir_existe(self, domain_path: Path):
        """Domain directory deve existir."""
        assert domain_path.exists(), f"Domain não encontrado: {domain_path}"
        assert domain_path.is_dir(), f"Domain não é diretório: {domain_path}"
    
    def test_domain_init_existe(self, domain_path: Path):
        """Domain __init__.py deve existir."""
        init_file = domain_path / "__init__.py"
        assert init_file.exists(), f"__init__.py não encontrado: {init_file}"


# =============================================================================
# TESTES — ENTITIES
# =============================================================================

class TestEntities:
    """Valida existência das entidades."""
    
    ENTITIES_OBRIGATORIAS = [
        "agent.py",
        "conversation.py",
        "insight.py",
        "forecast.py",
        "tenant.py",
    ]
    
    def test_entities_dir_existe(self, domain_path: Path):
        """Diretório de entidades deve existir."""
        entities_dir = domain_path / "entities"
        assert entities_dir.exists(), f"entities/ não encontrado: {entities_dir}"
    
    @pytest.mark.parametrize("entity", ENTITIES_OBRIGATORIAS)
    def test_entity_existe(self, domain_path: Path, entity: str):
        """Entidade obrigatória deve existir."""
        entity_path = domain_path / "entities" / entity
        assert entity_path.exists(), f"Entidade não encontrada: {entity_path}"
    
    @pytest.mark.parametrize("entity", ENTITIES_OBRIGATORIAS)
    def test_entity_nao_vazia(self, domain_path: Path, entity: str):
        """Entidade não deve estar vazia."""
        entity_path = domain_path / "entities" / entity
        if entity_path.exists():
            content = entity_path.read_text(encoding="utf-8")
            assert len(content) > 100, f"Entidade muito curta: {entity_path}"


# =============================================================================
# TESTES — VALUE OBJECTS
# =============================================================================

class TestValueObjects:
    """Valida existência dos value objects."""
    
    VALUE_OBJECTS_OBRIGATORIOS = [
        "tenant_id.py",
        "user_id.py",
        "message_id.py",
        "time_range.py",
    ]
    
    def test_value_objects_dir_existe(self, domain_path: Path):
        """Diretório de value objects deve existir."""
        vo_dir = domain_path / "value_objects"
        assert vo_dir.exists(), f"value_objects/ não encontrado: {vo_dir}"
    
    @pytest.mark.parametrize("vo", VALUE_OBJECTS_OBRIGATORIOS)
    def test_value_object_existe(self, domain_path: Path, vo: str):
        """Value object obrigatório deve existir."""
        vo_path = domain_path / "value_objects" / vo
        assert vo_path.exists(), f"Value object não encontrado: {vo_path}"


# =============================================================================
# TESTES — PORTS
# =============================================================================

class TestPorts:
    """Valida existência dos ports (interfaces)."""
    
    PORTS_OBRIGATORIOS = [
        "llm_port.py",
        "data_source_port.py",
        "cache_port.py",
        "auth_port.py",
        "metrics_port.py",
        "agent_port.py",
    ]
    
    def test_ports_dir_existe(self, domain_path: Path):
        """Diretório de ports deve existir."""
        ports_dir = domain_path / "ports"
        assert ports_dir.exists(), f"ports/ não encontrado: {ports_dir}"
    
    @pytest.mark.parametrize("port", PORTS_OBRIGATORIOS)
    def test_port_existe(self, domain_path: Path, port: str):
        """Port obrigatório deve existir."""
        port_path = domain_path / "ports" / port
        assert port_path.exists(), f"Port não encontrado: {port_path}"
    
    @pytest.mark.parametrize("port", PORTS_OBRIGATORIOS)
    def test_port_tem_classe_abc(self, domain_path: Path, port: str):
        """Port deve conter classe ABC."""
        port_path = domain_path / "ports" / port
        if port_path.exists():
            content = port_path.read_text(encoding="utf-8")
            assert "ABC" in content, f"Port sem ABC: {port_path}"
            assert "abstractmethod" in content, f"Port sem abstractmethod: {port_path}"


# =============================================================================
# TESTES — DOCKER
# =============================================================================

class TestDockerFiles:
    """Valida existência dos arquivos Docker."""
    
    def test_dockerfile_existe(self, backend_path: Path):
        """Dockerfile deve existir."""
        dockerfile = backend_path / "Dockerfile"
        assert dockerfile.exists(), f"Dockerfile não encontrado: {dockerfile}"
    
    def test_dockerfile_nao_vazio(self, backend_path: Path):
        """Dockerfile não deve estar vazio."""
        dockerfile = backend_path / "Dockerfile"
        if dockerfile.exists():
            content = dockerfile.read_text(encoding="utf-8")
            assert len(content) > 200, f"Dockerfile muito curto: {dockerfile}"
            assert "FROM python" in content, "Dockerfile sem imagem base Python"
    
    def test_docker_compose_existe(self, backend_path: Path):
        """docker-compose.yml deve existir."""
        compose = backend_path / "docker-compose.yml"
        assert compose.exists(), f"docker-compose.yml não encontrado: {compose}"
    
    def test_docker_compose_tem_servicos(self, backend_path: Path):
        """docker-compose.yml deve ter serviços."""
        compose = backend_path / "docker-compose.yml"
        if compose.exists():
            content = compose.read_text(encoding="utf-8")
            assert "services:" in content, "docker-compose sem services"
            assert "api:" in content, "docker-compose sem serviço api"


# =============================================================================
# TESTES — DOCUMENTAÇÃO FASE 2
# =============================================================================

class TestDocumentacaoFase2:
    """Valida existência da documentação da FASE 2."""
    
    def test_arquitetura_alvo_existe(self):
        """Documento de arquitetura alvo deve existir."""
        doc_path = BASE_DIR / ".agent" / "docs" / "arquitetura_alvo.md"
        assert doc_path.exists(), f"arquitetura_alvo.md não encontrado: {doc_path}"
    
    def test_arquitetura_alvo_tem_diagramas(self):
        """Documento deve conter diagramas."""
        doc_path = BASE_DIR / ".agent" / "docs" / "arquitetura_alvo.md"
        if doc_path.exists():
            content = doc_path.read_text(encoding="utf-8")
            assert "```" in content, "Documento sem blocos de código"
            assert "LAYER" in content or "Layer" in content, "Documento sem menção a camadas"


# =============================================================================
# TESTES — CONTAGEM DE ARQUIVOS
# =============================================================================

class TestMetricasArquitetura:
    """Valida métricas mínimas da nova arquitetura."""
    
    def test_minimo_entities(self, domain_path: Path):
        """Deve haver pelo menos 5 entidades."""
        entities_dir = domain_path / "entities"
        if entities_dir.exists():
            count = len([f for f in entities_dir.iterdir() if f.suffix == ".py" and f.name != "__init__.py"])
            assert count >= 5, f"Poucas entidades: {count}"
    
    def test_minimo_value_objects(self, domain_path: Path):
        """Deve haver pelo menos 4 value objects."""
        vo_dir = domain_path / "value_objects"
        if vo_dir.exists():
            count = len([f for f in vo_dir.iterdir() if f.suffix == ".py" and f.name != "__init__.py"])
            assert count >= 4, f"Poucos value objects: {count}"
    
    def test_minimo_ports(self, domain_path: Path):
        """Deve haver pelo menos 6 ports."""
        ports_dir = domain_path / "ports"
        if ports_dir.exists():
            count = len([f for f in ports_dir.iterdir() if f.suffix == ".py" and f.name != "__init__.py"])
            assert count >= 6, f"Poucos ports: {count}"


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
