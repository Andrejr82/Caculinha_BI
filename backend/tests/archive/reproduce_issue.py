import asyncio
import sys
from langchain_core.messages import HumanMessage
from app.config.settings import settings
import logging

# Configure logging to catch full trace
logging.basicConfig(level=logging.DEBUG)

settings.LLM_PROVIDER = "mock"

from app.orchestration.graph import build_bi_agent_graph

async def reproduce():
    print("🚀 Reproducing error with query: 'gere um gráfico de vendas do produto 369947 em todas as lojas'")
    
    app = build_bi_agent_graph()
    query = "gere um gráfico de vendas do produto 369947 em todas as lojas"
    
    try:
        inputs = {"messages": [HumanMessage(content=query)]}
        # Using ainvoke to mimic ChatServiceV2
        result = await app.ainvoke(inputs)
        
        last = result["messages"][-1]
        print("✅ Result:", last.content)
        
    except Exception as e:
        print("❌ CRASH DETECTED:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
