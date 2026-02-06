
import asyncio
from dotenv import load_dotenv
import logging
import sys
import os

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

# Force reload
load_dotenv(override=True)

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.core.llm_factory import LLMFactory

logging.basicConfig(level=logging.INFO)

async def test_simple():
    print("--- Teste de Conectividade Gemini ---")
    try:
        # Forçar provider Google via SmartLLM
        llm = LLMFactory.get_adapter(provider="google", use_smart=True)
        print(f"Buscando adapter... SmartLLM primary: {llm.primary}")
        
        # O SmartLLM escolhe o adapter na hora do generate.
        # Vamos tentar acessar a propriedade .gemini para ver se instanciou
        if hasattr(llm, 'gemini'):
            print(f"Gemini Adapter status: {llm.gemini is not None}")
        
        response = await llm.generate_response("Olá, responda apenas 'GEMINI OK' se você for o Gemini.")
        print(f"Resposta recebida: {response}")
        
    except Exception as e:
        print(f"❌ Erro na chamada LLM: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple())
