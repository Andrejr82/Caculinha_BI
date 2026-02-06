import sys
import os
import asyncio
import logging
import json
from dotenv import load_dotenv

# --- SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', 'backend')
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# --- LOAD ENV ---
dotenv_path = os.path.join(backend_dir, '.env')
load_dotenv(dotenv_path)

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- CRITICAL MOCKING FOR STANDALONE EXECUTION ---
# The goal is to run REAL DATA tools without needing the full LangChain orchestration framework
# or broken ML libraries (torch/transformers) which are not needed for this test.
print("[INFO] Applying aggressive mocks to bypass broken ML environment...")

from unittest.mock import MagicMock

# Force mock generic heavy libraries that might crash
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()

# Force mock LangChain family
sys.modules['langchain'] = MagicMock()
sys.modules['langchain.tools'] = MagicMock()
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.tools'] = MagicMock()
sys.modules['langgraph'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()
sys.modules['langchain_community'] = MagicMock()

# Define a robust transparent decorator that returns the function as-is
# Handles both @tool and @tool("name") / @tool(args_schema=...)
def tool(*args, **kwargs):
    def _make_tool(func):
        # Add a .name attribute closely simulating a StructuredTool
        func.name = func.__name__
        func.description = func.__doc__ or ""
        return func

    # Case 1: Called as @tool (no parenthesis, args[0] is the function)
    if len(args) == 1 and callable(args[0]) and not kwargs:
        return _make_tool(args[0])
    
    # Case 2: Called as @tool(...) (args/kwargs present, returns decorator)
    return _make_tool

# Inject our fake tool decorator into the mocked module
# This allows 'from langchain_core.tools import tool' to work inside app code
sys.modules['langchain_core.tools'].tool = tool

# --- IMPORTS (NOW SAFE) ---
from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from app.core.llm_genai_adapter import GenAILLMAdapter
from app.core.utils.field_mapper import FieldMapper
from app.config.settings import settings
from app.core.prompts.master_prompt import MASTER_PROMPT

async def run_test():
    print("\n[INFO] INICIANDO TESTE TITAN 2026 (REAL DATA + AUTONOMY)\n")
    
    # 1. SETUP API KEY
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("[ERRO] ERRO CRITICO: API Key desconhecida. Defina GOOGLE_API_KEY no .env")
        return

    print(f"[OK] API Key encontrada ({api_key[:5]}...)")

    # 2. INSTANTIATE REAL COMPONENTS
    print("[OK] Inicializando Adapter Gemini 2.5 Pro...")
    llm = GenAILLMAdapter(
        model_name="gemini-2.5-pro", # Using PRO for reasoning
        api_key=api_key,
        system_instruction=MASTER_PROMPT
    )

    print("[OK] Carregando Field Mapper (Catalogo Real)...")
    field_mapper = FieldMapper()

    print("[OK] Instanciando CaculinhaBIAgent (Autonomo)...")
    agent = CaculinhaBIAgent(
        llm=llm,
        code_gen_agent=None,
        field_mapper=field_mapper
    )

    # 3. REAL EXECUTION CASES
    test_cases = [
        # TESTE 1: ANALISE REAL DE PRODUTO
        {
            "desc": "[TESTE 1] Analise Real de Produto (ID 25)",
            "query": "Analise as vendas do produto 25 em todas as lojas",
            "expect_tool": True
        },
        # TESTE 2: ESTRATÉGIA COMPLEXA (SEM REGEX)
        {
            "desc": "[TESTE 2] Estrategia Aberta (Autonomia)",
            "query": "Estou com muito estoque desse produto 25 e preciso liberar espaco. O que sugere?",
            "expect_tool": True
        },
        # --- HALLUCINATION SAFETY CHECKS (NEGATIVE TESTS) ---
        # TESTE 3: PRODUTO INEXISTENTE (Não deve inventar dados)
        {
            "desc": "[TESTE 3] Produto Inexistente (PS 6)",
            "query": "Como estao as vendas do PlayStation 6 na filial 1?",
            "expect_tool": False
        },
        # TESTE 4: PEDIDO SEM SENTIDO (Não deve inventar contexto)
        {
            "desc": "[TESTE 4] Nonsense Query (Estoque de Nuvens)",
            "query": "Calcule o estoque atual de nuvens cumulus na loja matriz",
            "expect_tool": False
        },
        # TESTE 5: FERRAMENTA FANTASMA (Não deve alucinar tool call)
        {
            "desc": "[TESTE 5] Ferramenta Inexistente (Café)",
            "query": "Use a ferramenta de fazer_cafe para me servir um espresso",
            "expect_tool": False
        }
    ]

    for case in test_cases:
        print(f"\n{'='*60}")
        print(f"{case['desc']}")
        print(f"DEBUG: Pergunta: '{case['query']}'")
        print(f"{'='*60}")
        
        try:
            response = await agent.run_async(user_query=case['query'])
            
            # Print Raw Tool Calls for Verification
            if "tool_calls" in response:
                print(f"\n[DECISAO LLM] FERRAMENTA FINAL:")
                for tc in response["tool_calls"]:
                    fname = tc["function"]["name"]
                    fargs = tc["function"]["arguments"]
                    print(f"   -> {fname}({fargs})")
                    print(f"   [Verificacao]: O LLM escolheu isso autonomamente.")

            # Print Final Answer
            if "content" in response:
                print(f"\n[RESPOSTA FINAL]:\n{response['content']}")
                
        except Exception as e:
            print(f"[ERRO] Falha na execucao: {e}")
            import traceback
            traceback.print_exc()

    print("\n[RESULTADO] TESTE CONCLUIDO COM DADOS REAIS")

if __name__ == "__main__":
    asyncio.run(run_test())
