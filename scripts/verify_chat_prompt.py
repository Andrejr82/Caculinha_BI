
import asyncio
import sys
import logging
import os

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from app.core.llm_factory import LLMFactory
from app.core.utils.field_mapper import FieldMapper

logging.basicConfig(level=logging.INFO)

async def test_chat_persona():
    print("--- Testando Persona do Chat (System Prompt) ---")
    
    # 1. Instancia Agente
    try:
        llm = LLMFactory.get_adapter(use_smart=True)
        field_mapper = FieldMapper()
        # Mock de dependências não essenciais para este teste
        agent = CaculinhaBIAgent(
            llm=llm,
            code_gen_agent=None, # Não precisamos para chat simples
            field_mapper=field_mapper,
            enable_rag=False # Desabilita RAG para focar no System Prompt puro
        )
        
        # 2. Pergunta de Controle
        question = "Qual seu papel e quais dados você tem acesso?"
        print(f"Pergunta: {question}")
        
        # 3. Executa
        response = await agent.run_async(user_query=question)
        
        print("\n--- Resposta ---")
        print(response)
        print("----------------")
        
        # 4. Validação
        # Se for dict, extrai apenas valores string para busca
        response_str = str(response)
        if isinstance(response, dict):
             # Tenta pegar 'output' ou 'response' ou converte tudo
             response_str = response.get("output", str(response))

        keywords = ["Caçulinha", "vendas", "estoque", "dados", "BI"]
        present = [k for k in keywords if k.lower() in response_str.lower()]
        print(f"\nKeywords encontradas: {present}")
        
        if len(present) >= 2:
            print("✅ Validação de Persona: SUCESSO")
        else:
            print("⚠️ Validação de Persona: INCERTO (Keywords insuficientes)")
            
    except Exception as e:
        print(f"Erro no teste do Chat: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_persona())
