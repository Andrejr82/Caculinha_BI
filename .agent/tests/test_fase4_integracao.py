"""
FASE 4 — Testes de Integração com Dados Reais

Este módulo contém testes de integração que validam os adapters
e agentes com dados REAIS (Parquet/DuckDB e Gemini API).

Uso:
    pytest tests/test_fase4_integracao.py -v

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from pathlib import Path

import pytest

# Configurar path do projeto
import sys
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Carregar variáveis de ambiente do .env
from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def parquet_dir() -> Path:
    """Retorna o diretório de arquivos Parquet."""
    return BACKEND_DIR / "data" / "parquet"


@pytest.fixture
def duckdb_adapter():
    """Cria instância real do DuckDBAdapter."""
    from backend.infrastructure.adapters.data import DuckDBAdapter
    adapter = DuckDBAdapter()
    yield adapter
    adapter.close()


@pytest.fixture
def gemini_adapter():
    """Cria instância real do GeminiAdapter."""
    from backend.infrastructure.adapters.llm import GeminiAdapter
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY não configurada")
    
    return GeminiAdapter(api_key=api_key)


# =============================================================================
# TESTES — DUCKDB ADAPTER (DADOS REAIS)
# =============================================================================

class TestDuckDBAdapterReal:
    """Testes de integração do DuckDBAdapter com dados reais."""
    
    @pytest.mark.asyncio
    async def test_conexao_saudavel(self, duckdb_adapter):
        """Verifica se a conexão com DuckDB está funcionando."""
        result = await duckdb_adapter.health_check()
        assert result is True, "DuckDB health check falhou"
    
    @pytest.mark.asyncio
    async def test_listar_tabelas(self, duckdb_adapter):
        """Verifica se as tabelas Parquet são carregadas."""
        tables = await duckdb_adapter.get_tables()
        assert isinstance(tables, list), "get_tables deve retornar lista"
        print(f"\nTabelas encontradas: {tables}")
        # admmat deve existir baseado no find anterior
        if tables:
            assert any("admmat" in t.lower() for t in tables), "Tabela admmat não encontrada"
    
    @pytest.mark.asyncio
    async def test_query_simples(self, duckdb_adapter):
        """Executa query simples nos dados reais."""
        tables = await duckdb_adapter.get_tables()
        if not tables:
            pytest.skip("Nenhuma tabela disponível")
        
        table = tables[0]
        result = await duckdb_adapter.execute_query(f"SELECT * FROM {table} LIMIT 5")
        
        assert result.row_count <= 5, "Limite não respeitado"
        assert len(result.columns) > 0, "Nenhuma coluna retornada"
        print(f"\nColunas de {table}: {result.columns}")
        print(f"Primeiros registros: {result.data[:2]}")
    
    @pytest.mark.asyncio
    async def test_contagem_registros(self, duckdb_adapter):
        """Conta registros em tabela real."""
        tables = await duckdb_adapter.get_tables()
        if not tables:
            pytest.skip("Nenhuma tabela disponível")
        
        table = tables[0]
        count = await duckdb_adapter.get_row_count(table)
        
        assert count > 0, f"Tabela {table} está vazia"
        print(f"\nTotal de registros em {table}: {count:,}")
    
    @pytest.mark.asyncio
    async def test_descrever_colunas(self, duckdb_adapter):
        """Descreve colunas de tabela real."""
        tables = await duckdb_adapter.get_tables()
        if not tables:
            pytest.skip("Nenhuma tabela disponível")
        
        table = tables[0]
        columns = await duckdb_adapter.get_columns(table)
        
        assert len(columns) > 0, "Nenhuma coluna descrita"
        print(f"\nSchema de {table}:")
        for col in columns[:10]:
            print(f"  - {col.name}: {col.dtype}")


# =============================================================================
# TESTES — GEMINI ADAPTER (API REAL)
# =============================================================================

class TestGeminiAdapterReal:
    """Testes de integração do GeminiAdapter com API real."""
    
    @pytest.mark.asyncio
    async def test_modelo_configurado(self, gemini_adapter):
        """Verifica se o modelo está configurado."""
        model_name = gemini_adapter.get_model_name()
        assert "gemini" in model_name.lower(), f"Modelo inesperado: {model_name}"
        print(f"\nModelo: {model_name}")
    
    @pytest.mark.asyncio
    async def test_geracao_simples(self, gemini_adapter):
        """Testa geração de texto simples."""
        messages = [
            {"role": "user", "content": "Responda apenas: Olá, estou funcionando!"}
        ]
        
        response = await gemini_adapter.generate(messages, temperature=0.1)
        
        assert response.content, "Resposta vazia"
        assert len(response.content) > 5, "Resposta muito curta"
        print(f"\nResposta do Gemini: {response.content[:200]}")
        
        if response.usage:
            print(f"Tokens usados: {response.usage}")
    
    @pytest.mark.asyncio
    async def test_contagem_tokens(self, gemini_adapter):
        """Testa contagem de tokens."""
        text = "Este é um teste de contagem de tokens no Gemini."
        
        count = await gemini_adapter.count_tokens(text)
        
        assert count > 0, "Contagem de tokens falhou"
        print(f"\nTexto: '{text}'")
        print(f"Tokens: {count}")


# =============================================================================
# TESTES — AGENTES INTEGRADOS (DADOS REAIS)
# =============================================================================

class TestAgentesIntegrados:
    """Testes de integração dos agentes com adapters reais."""
    
    @pytest.mark.asyncio
    async def test_sql_agent_com_dados_reais(self, duckdb_adapter, gemini_adapter):
        """Testa SQLAgent com dados reais."""
        from backend.application.agents import SQLAgent
        from backend.domain.ports.agent_port import AgentRequest
        
        agent = SQLAgent(llm=gemini_adapter, data_source=duckdb_adapter)
        
        # Verificar tabelas disponíveis
        tables = await duckdb_adapter.get_tables()
        if not tables:
            pytest.skip("Nenhuma tabela disponível")
        
        request = AgentRequest(
            message=f"Liste as primeiras 3 colunas da tabela {tables[0]}",
            conversation_id="test-conv",
            tenant_id="test-tenant",
            user_id="test-user",
        )
        
        response = await agent.run(request)
        
        assert response.agent_name == "SQLAgent"
        print(f"\nResposta do SQLAgent:\n{response.content[:500]}")
    
    @pytest.mark.asyncio
    async def test_metadata_agent_com_dados_reais(self, duckdb_adapter):
        """Testa MetadataAgent com dados reais."""
        from backend.application.agents import MetadataAgent
        from backend.domain.ports.agent_port import AgentRequest
        
        agent = MetadataAgent(data_source=duckdb_adapter)
        
        request = AgentRequest(
            message="Quais tabelas estão disponíveis?",
            conversation_id="test-conv",
            tenant_id="test-tenant",
            user_id="test-user",
        )
        
        response = await agent.run(request)
        
        assert response.success
        assert response.agent_name == "MetadataAgent"
        print(f"\nResposta do MetadataAgent:\n{response.content[:500]}")
    
    @pytest.mark.asyncio
    async def test_monitoring_agent(self):
        """Testa MonitoringAgent com métricas reais do sistema."""
        from backend.application.agents import MonitoringAgent
        from backend.domain.ports.agent_port import AgentRequest
        
        agent = MonitoringAgent()
        
        request = AgentRequest(
            message="Qual o status do sistema?",
            conversation_id="test-conv",
            tenant_id="test-tenant",
            user_id="test-user",
        )
        
        response = await agent.run(request)
        
        assert response.success
        assert "CPU" in response.content or "Memória" in response.content
        print(f"\nResposta do MonitoringAgent:\n{response.content}")


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
