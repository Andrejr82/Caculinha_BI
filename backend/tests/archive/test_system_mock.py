import asyncio
import sys
import os
from langchain_core.messages import HumanMessage
from app.config.settings import settings

# Force reload settings to ensure 'mock' is active if it was cached
import importlib
import app.config.settings
importlib.reload(app.config.settings)

# Import graph after settings (to pick up changes if any, though env vars are sticky)
from app.orchestration.graph import build_bi_agent_graph

async def verify_system_mock():
    print(f"🔧 CONFIG ATUAL: LLM_PROVIDER={settings.LLM_PROVIDER}")
    
    if settings.LLM_PROVIDER != "mock":
        print("❌ ERRO: O provider deveria ser 'mock'.")
        return

    print("🚀 Construindo Grafo...")
    app = build_bi_agent_graph()
    
    query = "qual é o preço do produto 369947?"
    print(f"📝 Query: {query}")
    
    try:
        inputs = {"messages": [HumanMessage(content=query)]}
        result = await app.ainvoke(inputs)
        
        last_msg = result["messages"][-1]
        print(f"📄 Resposta Final: {last_msg.content[:200]}...")
        
        if "Gerado via Arquitetura Local" in last_msg.content:
            print("✅ SUCESSO! O MockLLM do sistema respondeu.")
        else:
            print(f"⚠️ AVISO: A resposta não parece vir do MockLLM padrão.")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_system_mock())
