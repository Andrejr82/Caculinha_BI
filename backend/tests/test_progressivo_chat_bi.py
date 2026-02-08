"""
Plano de Testes Progressivo: Chat BI
Metodologia: Test Engineer (Debugging Sistemático)

Objetivo: Identificar EXATAMENTE onde a resposta está ficando vazia.

Estratégia: Testes progressivos do mais simples ao mais complexo.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.chat_service_v3 import ChatServiceV3
from backend.app.core.utils.session_manager import SessionManager
from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.llm_factory import LLMFactory
from backend.app.core.utils.field_mapper import FieldMapper
from backend.app.core.agents.code_gen_agent import CodeGenAgent


class TestProgressivo:
    """
    Testes progressivos para identificar onde a resposta fica vazia.
    
    Ordem de execução:
    1. LLM direto
    2. Agente isolado
    3. ChatServiceV3
    4. Endpoint SSE (manual)
    """
    
    @pytest.mark.asyncio
    async def test_1_llm_direto(self):
        """
        TESTE 1: LLM responde diretamente?
        
        Objetivo: Verificar se o LLM está funcionando.
        """
        print("\n" + "="*60)
        print("TESTE 1: LLM DIRETO")
        print("="*60)
        
        llm = LLMFactory.get_adapter(use_smart=True)
        
        messages = [
            {"role": "user", "content": "Diga 'olá' em uma palavra"}
        ]
        
        # FIX: SmartLLM usa get_completion(), não chat()
        response = llm.get_completion(messages)
        
        print(f"✅ LLM Response Type: {type(response)}")
        print(f"✅ LLM Response: {response}")
        
        assert response is not None
        assert isinstance(response, dict)
        assert "content" in response or "error" not in response
        print("✅ TESTE 1 PASSOU: LLM funciona!")
    
    @pytest.mark.asyncio
    async def test_2_agente_isolado(self):
        """
        TESTE 2: Agente retorna resposta?
        
        Objetivo: Verificar se o CaculinhaBIAgent está funcionando.
        """
        print("\n" + "="*60)
        print("TESTE 2: AGENTE ISOLADO")
        print("="*60)
        
        llm = LLMFactory.get_adapter(use_smart=True)
        code_gen = CodeGenAgent()
        field_mapper = FieldMapper()
        
        agent = CaculinhaBIAgent(
            llm=llm,
            code_gen_agent=code_gen,
            field_mapper=field_mapper,
            user_role="analyst",
            enable_rag=True
        )
        
        # Query simples
        query = "Olá"
        history = []
        
        response = await agent.run_async(query, history)
        
        print(f"✅ Agent Response Type: {type(response)}")
        print(f"✅ Agent Response Keys: {response.keys() if isinstance(response, dict) else 'NOT A DICT'}")
        print(f"✅ Agent Response: {str(response)[:500]}")
        
        assert response is not None
        assert isinstance(response, dict)
        
        # Verificar se tem alguma chave com conteúdo
        has_content = False
        for key in ['response', 'text_override', 'result', 'mensagem']:
            if key in response and response[key]:
                print(f"✅ Encontrado conteúdo em '{key}': {str(response[key])[:100]}")
                has_content = True
                break
        
        assert has_content, f"❌ NENHUMA CHAVE COM CONTEÚDO! Keys: {response.keys()}"
        print("✅ TESTE 2 PASSOU: Agente retorna conteúdo!")
    
    @pytest.mark.asyncio
    async def test_3_chat_service_simples(self):
        """
        TESTE 3: ChatServiceV3 processa query simples?
        
        Objetivo: Verificar se o ChatServiceV3 está processando corretamente.
        """
        print("\n" + "="*60)
        print("TESTE 3: CHAT SERVICE V3")
        print("="*60)
        
        session_manager = SessionManager(storage_dir="app/data/sessions")
        service = ChatServiceV3(session_manager=session_manager)
        
        query = "Olá"
        session_id = "test_session"
        user_id = "test_user"
        
        result = await service.process_message(
            query=query,
            session_id=session_id,
            user_id=user_id
        )
        
        print(f"✅ Service Result Type: {type(result)}")
        print(f"✅ Service Result Keys: {result.keys() if isinstance(result, dict) else 'NOT A DICT'}")
        print(f"✅ Service Result: {str(result)[:500]}")
        
        assert result is not None
        assert isinstance(result, dict)
        assert "result" in result
        assert "mensagem" in result["result"]
        
        mensagem = result["result"]["mensagem"]
        print(f"✅ Mensagem extraída: {mensagem[:200]}")
        
        assert mensagem != "", "❌ MENSAGEM VAZIA!"
        assert len(mensagem.strip()) > 0, "❌ MENSAGEM SÓ TEM WHITESPACE!"
        
        print("✅ TESTE 3 PASSOU: ChatServiceV3 funciona!")
    
    @pytest.mark.asyncio
    async def test_4_chat_service_query_real(self):
        """
        TESTE 4: ChatServiceV3 processa query real de BI?
        
        Objetivo: Testar com query real que usa ferramentas.
        """
        print("\n" + "="*60)
        print("TESTE 4: QUERY REAL DE BI")
        print("="*60)
        
        session_manager = SessionManager(storage_dir="app/data/sessions")
        service = ChatServiceV3(session_manager=session_manager)
        
        query = "Qual o estoque do produto 369947?"
        session_id = "test_session_real"
        user_id = "test_user"
        
        result = await service.process_message(
            query=query,
            session_id=session_id,
            user_id=user_id
        )
        
        print(f"✅ Service Result: {str(result)[:1000]}")
        
        assert result is not None
        assert isinstance(result, dict)
        assert "result" in result
        assert "mensagem" in result["result"]
        
        mensagem = result["result"]["mensagem"]
        print(f"✅ Mensagem: {mensagem[:500]}")
        
        assert mensagem != "", "❌ MENSAGEM VAZIA PARA QUERY REAL!"
        assert len(mensagem.strip()) > 0, "❌ MENSAGEM SÓ TEM WHITESPACE!"
        
        # Verificar se tem conteúdo relevante
        assert len(mensagem) > 20, f"❌ MENSAGEM MUITO CURTA: {mensagem}"
        
        print("✅ TESTE 4 PASSOU: Query real funciona!")


# Executar testes
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
