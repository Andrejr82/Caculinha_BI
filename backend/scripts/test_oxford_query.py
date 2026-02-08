
import asyncio
import os
import sys

# Adicionar raiz ao path
sys.path.append(os.getcwd())

from backend.app.services.chat_service_v3 import ChatServiceV3
from backend.app.core.utils.session_manager import SessionManager
from backend.app.core.tools.universal_chart_generator import gerar_grafico_universal_v2

async def test_oxford():
    print("--- Teste Grupo Oxford ---")
    session_manager = SessionManager()
    chat_service = ChatServiceV3(session_manager=session_manager)
    
    query = "como estao as vendas do grupo oxford em todas as lojas"
    session_id = "test_oxford_session"
    user_id = "tester"
    
    try:
        response = await chat_service.process_message(query, session_id, user_id)
        print("\n\nRESPOSTA DO AGENTE:")
        print(response.get("result", {}).get("mensagem", "Sem mensagem"))
        
        # Verificar se identificou Oxford
        print("\n\nVERIFICAÇÃO INTERNA:")
        # A verificação interna real dependeria de logs, mas vamos julgar pela resposta.
        # Se a resposta mencionar "Oxford", sucesso. Se mencionar "Chamex" como top líder sem citar Oxford, falha.
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_oxford())
