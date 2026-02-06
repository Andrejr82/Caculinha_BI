import logging
import asyncio
import sys
from pathlib import Path

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to sys.path
sys.path.append(str(Path(__file__).parent))

from app.services.chat_service_v3 import ChatServiceV3
from app.core.utils.session_manager import SessionManager

async def test_deep_knowledge():
    print("=== INICIANDO TESTE DECEP KNOWLEDGE (1000% CHECK) ===")
    
    # Mock session manager
    session_manager = SessionManager()
    
    # Init Service
    service = ChatServiceV3(session_manager)
    
    queries = [
        # Teste 1: Conhecimento do Schema (System Prompt Injection)
        "Quais colunas você tem acesso no banco de dados?",
        
        # Teste 2: Extração de Entidade via LLM (Grupo FERRAGEM não está no regex)
        "Qual o total de vendas do grupo FERRAGEM?",
        
        # Teste 3: Regressão Simples
        "Vendas do produto 59294?"
    ]
    
    for q in queries:
        print(f"\n--- QUERY: {q} ---")
        try:
            # Mock user/session
            import uuid
            valid_uuid = str(uuid.uuid4())
            result = await service.process_message(q, valid_uuid, "user_1")
            
            # Print Result
            print(f"RESPOSTA TYPE: {result.get('response_type')}")
            print(f"MENSAGEM: {result['result']['mensagem'][:200]}...") # Truncado
            
            # Validação
            if "colunas" in q.lower():
                # Espera-se que mencione colunas reais
                if "PRODUTO" in result['result']['mensagem'] or "NOME" in result['result']['mensagem']:
                    print("[OK] TESTE 1 (SCHEMA): PASSOU")
                else:
                    print("[FAIL] TESTE 1 (SCHEMA): FALHOU (Nao listou colunas)")
            
            if "FERRAGEM" in q:
                # Espera-se que tenha calculado ou explicado
                if "R$" in result['result']['mensagem'] or "vendas" in result['result']['mensagem'].lower():
                     print("[OK] TESTE 2 (LLM ENTITY): PASSOU")
                else:
                     print("[FAIL] TESTE 2 (LLM ENTITY): FALHOU")

        except Exception as e:
            print(f"[ERROR] ERRO GRAVE: {e}")
            import traceback
            traceback.print_exc()

    service.close()

if __name__ == "__main__":
    asyncio.run(test_deep_knowledge())
