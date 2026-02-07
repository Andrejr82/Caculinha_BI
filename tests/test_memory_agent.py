"""
Testes para MemoryAgent e Adapters

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import tempfile
import os

# Importar entidades
from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message
from backend.domain.entities.memory_entry import MemoryEntry


# =============================================================================
# TESTES DE ENTIDADES
# =============================================================================

class TestConversation:
    """Testes para a entidade Conversation."""
    
    def test_create_conversation(self):
        """Deve criar conversa com campos obrigatórios."""
        conv = Conversation(
            tenant_id="tenant-1",
            user_id="user-1",
        )
        
        assert conv.id.startswith("conv-")
        assert conv.tenant_id == "tenant-1"
        assert conv.user_id == "user-1"
        assert conv.title is None
        assert isinstance(conv.created_at, datetime)
    
    def test_conversation_to_dict(self):
        """Deve serializar conversa para dicionário."""
        conv = Conversation(
            id="conv-test-123",
            tenant_id="tenant-1",
            user_id="user-1",
            title="Minha conversa",
        )
        
        data = conv.to_dict()
        
        assert data["id"] == "conv-test-123"
        assert data["tenant_id"] == "tenant-1"
        assert data["title"] == "Minha conversa"
    
    def test_conversation_from_dict(self):
        """Deve deserializar conversa de dicionário."""
        data = {
            "id": "conv-abc",
            "tenant_id": "tenant-2",
            "user_id": "user-2",
            "title": "Teste",
            "created_at": "2026-02-07T10:00:00",
            "updated_at": "2026-02-07T11:00:00",
        }
        
        conv = Conversation.from_dict(data)
        
        assert conv.id == "conv-abc"
        assert conv.tenant_id == "tenant-2"
        assert conv.title == "Teste"
    
    def test_conversation_validation(self):
        """Deve validar campos obrigatórios."""
        with pytest.raises(ValueError, match="tenant_id is required"):
            Conversation(tenant_id="", user_id="user-1")
        
        with pytest.raises(ValueError, match="user_id is required"):
            Conversation(tenant_id="tenant-1", user_id="")


class TestMessage:
    """Testes para a entidade Message."""
    
    def test_create_message(self):
        """Deve criar mensagem com campos obrigatórios."""
        msg = Message(
            conversation_id="conv-1",
            role="user",
            content="Olá, como posso ajudar?",
        )
        
        assert msg.id.startswith("msg-")
        assert msg.conversation_id == "conv-1"
        assert msg.role == "user"
        assert msg.content == "Olá, como posso ajudar?"
    
    def test_message_factories(self):
        """Deve criar mensagens usando factories."""
        user_msg = Message.user("conv-1", "Pergunta do usuário")
        assistant_msg = Message.assistant("conv-1", "Resposta do assistente")
        system_msg = Message.system("conv-1", "Instrução do sistema")
        
        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"
        assert system_msg.role == "system"
    
    def test_message_to_llm_format(self):
        """Deve converter para formato LLM."""
        msg = Message.user("conv-1", "Texto da mensagem")
        
        llm_format = msg.to_llm_format()
        
        assert llm_format == {"role": "user", "content": "Texto da mensagem"}
    
    def test_message_token_estimate(self):
        """Deve estimar tokens."""
        msg = Message.user("conv-1", "a" * 100)
        
        # ~4 chars = 1 token
        assert msg.token_estimate == 25
    
    def test_message_validation(self):
        """Deve validar role inválido."""
        with pytest.raises(ValueError, match="Invalid role"):
            Message(conversation_id="conv-1", role="invalid", content="test")


class TestMemoryEntry:
    """Testes para a entidade MemoryEntry."""
    
    def test_create_memory_entry(self):
        """Deve criar entrada de memória."""
        entry = MemoryEntry(
            conversation_id="conv-1",
            message_id="msg-1",
            content="Conteúdo indexado",
            embedding=[0.1, 0.2, 0.3],
        )
        
        assert entry.id.startswith("mem-")
        assert entry.has_embedding is True
        assert entry.embedding_dimension == 3
    
    def test_memory_entry_from_message(self):
        """Deve criar entrada a partir de mensagem."""
        msg = Message.user("conv-1", "Texto da mensagem")
        embedding = [0.1] * 768
        
        entry = MemoryEntry.from_message(msg, embedding)
        
        assert entry.conversation_id == "conv-1"
        assert entry.message_id == msg.id
        assert entry.content == "Texto da mensagem"
        assert len(entry.embedding) == 768


# =============================================================================
# TESTES DE ADAPTERS
# =============================================================================

class TestSQLiteMemoryAdapter:
    """Testes para SQLiteMemoryAdapter."""
    
    @pytest.fixture
    def temp_db(self):
        """Cria banco de dados temporário."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)
    
    @pytest.fixture
    def adapter(self, temp_db):
        """Cria adapter com DB temporário."""
        from backend.infrastructure.adapters.memory import SQLiteMemoryAdapter
        return SQLiteMemoryAdapter(db_path=temp_db)
    
    @pytest.mark.asyncio
    async def test_save_and_get_conversation(self, adapter):
        """Deve salvar e recuperar conversa."""
        conv = Conversation(
            tenant_id="tenant-1",
            user_id="user-1",
            title="Teste SQLite",
        )
        
        # Salvar
        conv_id = await adapter.save_conversation(conv)
        
        # Recuperar
        retrieved = await adapter.get_conversation(conv_id)
        
        assert retrieved is not None
        assert retrieved.id == conv.id
        assert retrieved.title == "Teste SQLite"
    
    @pytest.mark.asyncio
    async def test_add_and_get_messages(self, adapter):
        """Deve adicionar e recuperar mensagens."""
        # Criar conversa
        conv = Conversation(tenant_id="t1", user_id="u1")
        await adapter.save_conversation(conv)
        
        # Adicionar mensagens
        msg1 = Message.user(conv.id, "Primeira mensagem")
        msg2 = Message.assistant(conv.id, "Segunda mensagem")
        
        await adapter.add_message(msg1)
        await adapter.add_message(msg2)
        
        # Recuperar
        messages = await adapter.get_recent_messages(conv.id, limit=10)
        
        assert len(messages) == 2
        assert messages[0].content == "Primeira mensagem"
        assert messages[1].content == "Segunda mensagem"
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, adapter):
        """Deve deletar conversa e mensagens."""
        # Criar
        conv = Conversation(tenant_id="t1", user_id="u1")
        await adapter.save_conversation(conv)
        await adapter.add_message(Message.user(conv.id, "Mensagem"))
        
        # Deletar
        deleted = await adapter.delete_conversation(conv.id)
        
        assert deleted is True
        
        # Verificar
        retrieved = await adapter.get_conversation(conv.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_list_conversations(self, adapter):
        """Deve listar conversas por tenant."""
        # Criar várias conversas
        for i in range(5):
            conv = Conversation(
                tenant_id="tenant-list",
                user_id=f"user-{i}",
                title=f"Conv {i}",
            )
            await adapter.save_conversation(conv)
        
        # Listar
        conversations = await adapter.list_conversations(
            tenant_id="tenant-list",
            limit=10,
        )
        
        assert len(conversations) == 5
    
    @pytest.mark.asyncio
    async def test_count_messages(self, adapter):
        """Deve contar mensagens."""
        conv = Conversation(tenant_id="t1", user_id="u1")
        await adapter.save_conversation(conv)
        
        for i in range(3):
            await adapter.add_message(Message.user(conv.id, f"Msg {i}"))
        
        count = await adapter.count_messages(conv.id)
        
        assert count == 3


# =============================================================================
# TESTES DO MEMORY AGENT
# =============================================================================

class TestMemoryAgent:
    """Testes para MemoryAgent."""
    
    @pytest.fixture
    def temp_db(self):
        """Cria banco de dados temporário."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        if os.path.exists(f.name):
            os.unlink(f.name)
    
    @pytest.fixture
    def memory_agent(self, temp_db):
        """Cria MemoryAgent com SQLite temporário."""
        from backend.infrastructure.adapters.memory import SQLiteMemoryAdapter
        from backend.application.agents.memory_agent import MemoryAgent
        
        adapter = SQLiteMemoryAdapter(db_path=temp_db)
        return MemoryAgent(memory_repository=adapter)
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, memory_agent):
        """Deve criar nova conversa."""
        conv = await memory_agent.create_conversation(
            tenant_id="tenant-test",
            user_id="user-test",
            title="Conversa de teste",
        )
        
        assert conv.id.startswith("conv-")
        assert conv.tenant_id == "tenant-test"
        assert conv.title == "Conversa de teste"
    
    @pytest.mark.asyncio
    async def test_save_and_load_memory(self, memory_agent):
        """Deve salvar e carregar memória."""
        # Criar conversa
        conv = await memory_agent.create_conversation(
            tenant_id="t1",
            user_id="u1",
        )
        
        # Salvar memória
        result = await memory_agent.save_memory(
            conversation_id=conv.id,
            user_message="Qual o estoque do produto X?",
            assistant_message="O estoque do produto X é 150 unidades.",
            tenant_id="t1",
            user_id="u1",
        )
        
        assert "user_message_id" in result
        assert "assistant_message_id" in result
        
        # Carregar memória
        context = await memory_agent.load_memory(conv.id)
        
        assert len(context.recent_messages) == 2
        assert context.recent_messages[0].role == "user"
        assert context.recent_messages[1].role == "assistant"
    
    @pytest.mark.asyncio
    async def test_load_memory_context_methods(self, memory_agent):
        """Deve testar métodos de MemoryContext."""
        conv = await memory_agent.create_conversation(
            tenant_id="t1",
            user_id="u1",
        )
        
        await memory_agent.save_memory(
            conversation_id=conv.id,
            user_message="Mensagem de teste",
            assistant_message="Resposta de teste",
            tenant_id="t1",
            user_id="u1",
        )
        
        context = await memory_agent.load_memory(conv.id)
        
        # Testar to_prompt_context
        prompt = context.to_prompt_context()
        assert "Histórico Recente" in prompt
        assert "Mensagem de teste" in prompt
        
        # Testar to_messages_list
        messages = context.to_messages_list()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_delete_conversation_via_agent(self, memory_agent):
        """Deve deletar conversa via agent."""
        conv = await memory_agent.create_conversation(
            tenant_id="t1",
            user_id="u1",
        )
        
        await memory_agent.save_memory(
            conversation_id=conv.id,
            user_message="Teste",
            assistant_message="Resposta",
        )
        
        # Deletar
        deleted = await memory_agent.delete_conversation(conv.id)
        
        assert deleted is True
        
        # Verificar que não existe mais
        context = await memory_agent.load_memory(conv.id)
        assert context.conversation is None
    
    @pytest.mark.asyncio
    async def test_list_conversations_via_agent(self, memory_agent):
        """Deve listar conversas via agent."""
        # Criar conversas
        for i in range(3):
            await memory_agent.create_conversation(
                tenant_id="tenant-list",
                user_id=f"user-{i}",
            )
        
        # Listar
        conversations = await memory_agent.list_conversations(
            tenant_id="tenant-list",
        )
        
        assert len(conversations) == 3


# =============================================================================
# MARCADORES PYTEST
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
