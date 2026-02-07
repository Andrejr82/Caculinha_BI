"""
conftest.py — Fixtures Globais de Testes

Autor: Testing Agent
Data: 2026-02-07
"""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture(scope="session")
def temp_data_dir():
    """Diretório temporário para dados de teste."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_conversation():
    """Conversa de exemplo para testes."""
    from backend.domain.entities.conversation import Conversation
    return Conversation(
        tenant_id="test-tenant",
        user_id="test-user",
        title="Test Conversation",
    )


@pytest.fixture
def sample_messages():
    """Mensagens de exemplo para testes."""
    from backend.domain.entities.message import Message
    return [
        Message.user("conv-test", "Olá, como estão as vendas?"),
        Message.assistant("conv-test", "As vendas estão em alta!"),
        Message.user("conv-test", "E o estoque?"),
    ]


@pytest.fixture
def sample_documents():
    """Documentos de exemplo para testes."""
    from backend.domain.entities.document import Document
    return [
        Document(tenant_id="test", content="Relatório de vendas Q1 2026"),
        Document(tenant_id="test", content="Análise de estoque janeiro"),
        Document(tenant_id="test", content="Projeção de demanda fevereiro"),
    ]


@pytest.fixture
def mock_llm_client():
    """Mock do cliente LLM."""
    from unittest.mock import AsyncMock
    client = AsyncMock()
    client.generate = AsyncMock(return_value="Resposta mockada do LLM")
    return client
