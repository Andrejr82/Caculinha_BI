"""
Debug do Loop Infinito no Agente
Simula a pergunta que causou RecursionLimit para ver o trace de ferramentas.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

async def debug_recursion():
    print("=== DEBUG RECURSION LIMIT ===")
    
    try:
        from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
        from app.infrastructure.database.models import User
        
        # Mock user
        user = User(username="debug_user", id=None, role="admin")
        
        agent = CaculinhaBIAgent()
        query = "Mostre o ranking completo dos top 20 produtos mais vendidos com análise detalhada"
        
        print(f"\n[Prompt] {query}")
        print("-" * 50)
        
        # Vamos rodar passo a passo se possível, ou capturar o log
        # O process_message do agente roda o grafo
        response = await agent.process_message(query, user, thread_id="debug_thread_001")
        
        print("\n[Resposta Final]")
        print(response)

    except Exception as e:
        print(f"\n[ERRO CAPTURADO] {e}")
        # Se for recursion limit, queremos ver isso
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_recursion())
