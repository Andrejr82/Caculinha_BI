import asyncio
import sys
import os
import json
from langchain_core.messages import HumanMessage
from app.config.settings import settings

# Force 'mock' just in case
settings.LLM_PROVIDER = "mock"

from app.orchestration.graph import build_bi_agent_graph

async def verify_offline_charts():
    print(f"🔧 CONFIG ATUAL: LLM_PROVIDER={settings.LLM_PROVIDER}")
    print("🚀 Construindo Grafo...")
    app = build_bi_agent_graph()
    
    # Test case: Chart
    query = "gráfico de vendas por grupo"
    print(f"\n📝 Query: {query}")
    
    try:
        inputs = {"messages": [HumanMessage(content=query)]}
        result = await app.ainvoke(inputs)
        
        last_msg = result["messages"][-1]
        content = last_msg.content
        
        print(f"📄 Resposta Final (Length: {len(content)}):")
        print(content[:500] + "..." if len(content) > 500 else content)
        
        # Verify if JSON block is present
        if "```json" in content and "chart_spec" in content:
            print("\n✅ SUCESSO! JSON de gráfico detectado na resposta.")
        else:
            print("\n❌ FALHA: Resposta não contém bloco JSON de gráfico esperado.")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_offline_charts())
