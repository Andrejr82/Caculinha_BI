
import asyncio
import os
import sys
from typing import Dict, Any, List

# Add backend to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Mocking LangChain dependencies to avoid import errors in standalone script
import builtins
from unittest.mock import MagicMock

class MockLangChain:
    def __getattr__(self, name):
        return MagicMock()

sys.modules["langchain"] = MockLangChain()
sys.modules["langchain_core"] = MockLangChain()
sys.modules["langchain_core.messages"] = MockLangChain()
sys.modules["langchain_core.prompts"] = MockLangChain()
sys.modules["langchain_core.runnables"] = MockLangChain()
sys.modules["langchain_core.tools"] = MockLangChain() # Added mock
sys.modules["langgraph"] = MockLangChain()
sys.modules["langgraph.graph"] = MockLangChain()
sys.modules["langgraph.prebuilt"] = MockLangChain()

# Import Agent (Local)
try:
    from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
    from app.core.llm_genai_adapter import GenAILLMAdapter
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def run_general_test():
    print("="*60)
    print("🛠️  INICIANDO BATERIA DE TESTES GERAIS (CAPACIDADE CORINGA)")
    print("="*60)

    # 1. Initialize Adapter & Agent
    # We use GenAILLMAdapter directly as verified previously
    try:
        adapter = GenAILLMAdapter(model_name="gemini-2.5-pro")
        
        # Mock dependencies
        mock_code_gen = MagicMock()
        mock_field_mapper = MagicMock()
        
        agent = CaculinhaBIAgent(
            llm=adapter, 
            code_gen_agent=mock_code_gen, 
            field_mapper=mock_field_mapper
        )
        print("[INFO] Agente inicializado com Sucesso (Gemini 2.5 Pro)")
    except Exception as e:
        print(f"[CRITICAL] Falha ao inicializar agente: {e}")
        return

    # 2. Define Test Questions
    questions = [
        {
            "category": "CONCEITUAL",
            "query": "O que significa Ruptura de Estoque e por que é ruim?",
            "expected_intent": "Explicação educativa"
        },
        {
            "category": "RACIOCINIO_SIMPLES",
            "query": "Se eu vendo um produto a 100 reais com margem de 30%, qual foi meu custo?",
            "expected_intent": "Cálculo matemático (70 reais) ou explicação da fórmula"
        },
        {
            "category": "SOCIAL_IDENTITY",
            "query": "Bom dia! Quem é você e o que você faz?",
            "expected_intent": "Identidade correta (IA BI / Lojas Caçula)"
        },
        {
            "category": "MIXED_CONTEXT",
            "query": "Como estão as vendas do setor de TECIDOS? E me explique o que fazer se estiverem baixas.",
            "expected_intent": "Tool call para dados + Texto de recomendação estratégica"
        }
    ]

    # 3. Open Report File
    with open("general_verification_report.txt", "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE CAPACIDADES GERAIS\n")
        f.write("===============================\n\n")

        for i, item in enumerate(questions):
            q = item["query"]
            cat = item["category"]
            print(f"\n[Running Test {i+1}/{len(questions)}] [{cat}]")
            print(f"Query: {q}")
            
            f.write(f"\n[TESTE {i+1}] Categoria: {cat}\n")
            f.write(f"Query: {q}\n")
            f.write(f"Expectativa: {item['expected_intent']}\n")

            try:
                # Run Agent
                response = await agent.run_async(user_query=q, chat_history=[])
                
                # Extract Result
                result_text = ""
                tool_usage = []

                # Handle dict response
                if isinstance(response, dict):
                    if response.get("type") == "text":
                        result_text = response.get("result")
                    elif response.get("type") == "code_result":
                        result_text = response.get("text_override") or str(response.get("result"))
                        tool_usage.append("code/chart")
                    
                    # Check for tool calls in internal history (not directly exposed in final dict usually, but inferred)
                    # For verify script simplicity, we look at the text.
                    # In a real run, run_async logs tool calls.
                
                print(f"RESULTADO: Recebida resposta de {len(str(result_text))} caracteres.")
                
                f.write("-" * 40 + "\n")
                f.write(f"[RESPOSTA AGENTE]:\n{result_text}\n")
                f.write("-" * 40 + "\n")
                
                if not result_text or len(result_text) < 10:
                     f.write("⚠️  ALERTA: Resposta muito curta ou vazia!\n")

            except Exception as e:
                print(f"❌ ERRO no teste {i+1}: {e}")
                f.write(f"❌ ERRO DE EXECUÇÃO: {e}\n")
                import traceback
                f.write(traceback.format_exc())

            f.flush()
            os.fsync(f.fileno())

    print("\n✅ Bateria de testes concluída. Verifique 'general_verification_report.txt'.")
    
    # Dump to stdout for tool to read
    print("\n--- CONTENT PREVIEW ---")
    with open("general_verification_report.txt", "r", encoding="utf-8") as f:
        print(f.read())
    print("-----------------------")

if __name__ == "__main__":
    asyncio.run(run_general_test())
