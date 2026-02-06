import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configuração de paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports Necessários
from langchain_core.messages import HumanMessage, AIMessage
from app.orchestration.graph import build_bi_agent_graph
from app.core.llm_factory import LLMFactory
from app.core.llm_langchain_adapter import CustomLangChainLLM

# MOCK LLM (Bypass total da API)
class MockLLM(CustomLangChainLLM):
    def __init__(self):
        # Inicializa sem adapter real
        pass
        
    def bind_tools(self, tools):
        return self
        
    def invoke(self, messages):
        # Simula comportamento do Agente:
        # 1. Se receber resultado de ferramenta (FunctionMessage/ToolMessage),
        #    retorna um texto final formatado.
        last_msg = messages[-1]
        
        if last_msg.type == "tool" or (isinstance(last_msg, dict) and last_msg.get("role") == "function"):
            return AIMessage(content=f"Recebi os dados da ferramenta. Aqui está o resultado:\n{last_msg.content}")
            
        # 2. Se for mensagem de usuário que FALHOU na heurística (não deveria acontecer neste teste),
        #    retorna erro simulado.
        return AIMessage(content="SOU UM MOCK: Não sei responder isso sem heurística.")

# Config Logging
logging.basicConfig(level=logging.ERROR)

# MONKEY PATCH: Substituir get_llm no módulo graph para usar nosso Mock
import app.orchestration.graph as graph_module

def mock_get_llm():
    print("🤖 [MOCK SYSTEM] Usando LLM Simulado (Custo Zero)")
    return MockLLM()

graph_module.get_llm = mock_get_llm

async def run_tests():
    print("\n" + "="*60)
    print(f"🚀 INICIANDO TESTES (DADOS REAIS - ZERO LLM)")
    print("="*60)

    # 1. Compilar Grafo (vai usar o MockLLM injetado)
    try:
        app = graph_module.build_bi_agent_graph()
        print("✅ Grafo compilado com MOCK LLM!")
    except Exception as e:
        print(f"❌ Erro ao compilar: {e}")
        return

    # 2. Cenários (Perguntas Reais do Usuário)
    # "qual é o preço do produto 369947?"
    # "qual é o estoque do produto 59294 na une 2365?"
    scenarios = [
        {
            "query": "qual é o preço do produto 369947?",
            "expectation": "Preço do produto 369947"
        },
        {
            "query": "qual é o estoque do produto 59294 na une 2365?",
            "expectation": "Estoque produto 59294 UNE 2365"
        }
    ]

    for i, scen in enumerate(scenarios):
        print(f"\n🔸 CENÁRIO {i+1}: '{scen['query']}'")
        
        inputs = {"messages": [HumanMessage(content=scen['query'])]}
        
        try:
            # Executar Grafo
            # Flasko Esperado:
            # 1. Heuristic Node -> Detecta Regex -> Retorna ToolCall (AIMessage)
            # 2. Tools Node -> Executa 'consultar_dados_flexivel' (LÊ PARQUET REAL) -> Retorna ToolMessage
            # 3. Agent Node (Mock) -> Recebe ToolMessage -> Retorna Texto Final
            
            result = await app.ainvoke(inputs)
            
            messages = result["messages"]
            
            # Verificar se houve Tool Call (Heurística)
            heuristic_msg = next((m for m in messages if isinstance(m, AIMessage) and m.tool_calls), None)
            if heuristic_msg:
                t_call = heuristic_msg.tool_calls[0]
                print(f"✅ Heurística Acionada: {t_call['name']}")
                print(f"   Args: {t_call['args']}")
            else:
                print("❌ Heurística FALHOU (foi pro Mock direto?)")

            # Verificar Resultado da Tool (Dados Reais)
            tool_msg = next((m for m in messages if m.type == "tool"), None)
            if tool_msg:
                print(f"✅ Ferramenta Executada (Dados Reais):")
                print(f"   Conteúdo: {tool_msg.content[:500]}...") # Print parcial
            else:
                print("❌ Ferramenta NÃO executada.")

            # Resposta Final
            final_msg = messages[-1]
            print(f"📄 Resposta Final (Mock): {final_msg.content}")

        except Exception as e:
            print(f"❌ Erro na execução: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("🏁 FIM DOS TESTES")

if __name__ == "__main__":
    asyncio.run(run_tests())
