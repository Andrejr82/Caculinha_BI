import asyncio
import os
import sys
import logging
from datetime import datetime

# Configuração de paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports do projeto
from langchain_core.messages import HumanMessage
from app.orchestration.graph import build_bi_agent_graph
from app.config.settings import settings

# Logging
logging.basicConfig(level=logging.ERROR) # Reduzir ruído interno, focar no print do teste
logger = logging.getLogger(__name__)

async def run_tests():
    # FORÇAR USO DO GOOGLE GEMINI (Bypassing Groq)
    settings.LLM_PROVIDER = "google"
    settings.LLM_MODEL_NAME = "gemini-2.5-flash-lite"
    
    print("\n" + "="*60)
    print(f"🚀 INICIANDO TESTES DO AGENTE LOCAL (SEM GROQ)")
    print("="*60)
    print(f"📅 Data: {datetime.now().isoformat()}")
    print(f"🤖 LLM Provider: {settings.LLM_PROVIDER}")
    print(f"🧠 Modelo Configurado: {settings.GROQ_MODEL_NAME}")
    print("="*60 + "\n")

    # 1. SETUP
    print("🔹 [SETUP] Inicializando Grafo LangGraph...")
    try:
        app = build_bi_agent_graph()
        print("✅ Grafo compilado com sucesso!")
    except Exception as e:
        print(f"❌ [ERRO CRÍTICO] Falha ao compilar grafo: {e}")
        return

    # 2. CENÁRIOS
    scenarios = [
        {
            "id": 1,
            "name": "TESTE HEURÍSTICA (Regex)",
            "query": "me mostre os produtos do fabricante OXFORD",
            "desc": "Deve ser interceptado pela heurística e NÃO chamar o LLM inicialmente."
        },
        {
            "id": 2,
            "name": "TESTE AGENTE (Raciocínio)",
            "query": "Analise o segmento FERRAMENTAS e aponte críticas de estoque",
            "desc": "Deve passar pelo LLM, usar ferramentas e retornar análise."
        }
    ]

    for cenario in scenarios:
        print(f"\n🔸 [{cenario['name']}]")
        print(f"📝 Query: '{cenario['query']}'")
        print(f"🎯 Objetivo: {cenario['desc']}")
        
        try:
            inputs = {"messages": [HumanMessage(content=cenario['query'])]}
            
            print("⏳ Executando...", end="", flush=True)
            start_time = datetime.now()
            
            # Executar grafo - invoke é síncrono no wrapper do LangGraph compilado, 
            # mas vamos ver se precisamos de ainvoke. O agent.py original usava invoke.
            # O build_bi_agent_graph retorna um CompiledGraph.
            result = await app.ainvoke(inputs)
            
            duration = (datetime.now() - start_time).total_seconds()
            print(f" (Concluído em {duration:.2f}s)")
            
            messages = result["messages"]
            last_msg = messages[-1]
            
            # Análise da Resposta Final
            print(f"📄 Resposta Final: {last_msg.content[:200]}..." if last_msg.content else "📄 Resposta Final: [Vazia/Tool Call]")
            
            # Verificar Heurística (Cenário 1)
            # Se for Heurística, a primeira mensagem AI deve ter tool_calls
            # E se foi rápido (< 1s), indica que não foi LLM.
            if cenario["id"] == 1:
                # Verificar tool_calls na primeira resposta AI
                ai_msgs = [m for m in messages if m.type == "ai"]
                if ai_msgs and hasattr(ai_msgs[0], "tool_calls") and ai_msgs[0].tool_calls:
                     # Se o ID começar com call_heuristic, é nosso sucesso
                     t_id = ai_msgs[0].tool_calls[0].get("id", "")
                     if "heuristic" in t_id:
                         print("✅ [SUCESSO] Heurística ativada corretamente (ID detectado).")
                     else:
                         print(f"⚠️ [ATENÇÃO] Tool call gerada, mas ID '{t_id}' não parece heurístico (LLM pode ter gerado).")
                else:
                     print("❌ [FALHA] Heurística não ativada (nenhuma tool call imediata).")

            # Verificar Agente (Cenário 2)
            if cenario["id"] == 2:
                # Devemos ter uso de ferramentas
                tool_msgs = [m for m in messages if m.type == "tool"]
                if tool_msgs:
                    print(f"✅ [SUCESSO] Ferramentas utilizadas: {len(tool_msgs)}")
                    for t in tool_msgs:
                        print(f"   - Tool: {t.name}")
                else:
                    print("⚠️ [AVISO] Nenhuma ferramenta foi chamada pelo Agente.")

            print("✅ Execução do cenário finalizada.")

        except Exception as e:
            print(f"❌ [ERRO] Falha na execução do cenário: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("🏁 TESTES CONCLUÍDOS")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_tests())
