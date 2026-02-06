import asyncio
import os
import sys
import json

# Adiciona o diretório raiz do backend ao path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_root)

# Carrega variáveis de ambiente
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_root, ".env"))

from app.config.settings import settings
from app.core.llm_gemini_adapter import GeminiLLMAdapter
from app.core.utils.field_mapper import FieldMapper
from app.core.rag.query_retriever import QueryRetriever
from app.core.learning.pattern_matcher import PatternMatcher
from app.core.utils.response_cache import ResponseCache
from app.core.utils.query_history import QueryHistory
from app.core.agents.code_gen_agent import CodeGenAgent
from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent, SYSTEM_PROMPT

async def test_graph_generation():
    print("--- Iniciando Teste de Geração de Gráfico (UNE 2365) ---")
    
    if not settings.GEMINI_API_KEY:
        print("ERRO: GEMINI_API_KEY não configurada no backend/.env")
        return

    print("Inicializando componentes...")
    llm = GeminiLLMAdapter(
        model_name=settings.LLM_MODEL_NAME,
        gemini_api_key=settings.GEMINI_API_KEY,
        system_instruction=SYSTEM_PROMPT
    )

    field_mapper = FieldMapper()
    query_retriever = QueryRetriever(
        embedding_model_name=settings.RAG_EMBEDDING_MODEL,
        faiss_index_path=settings.RAG_FAISS_INDEX_PATH,
        examples_path=settings.LEARNING_EXAMPLES_PATH
    )
    pattern_matcher = PatternMatcher()
    response_cache = ResponseCache(cache_dir="data/cache", ttl_minutes=settings.CACHE_TTL_MINUTES)
    query_history = QueryHistory(history_dir="data/query_history")
    
    code_gen_agent = CodeGenAgent(
        llm=llm,
        field_mapper=field_mapper,
        query_retriever=query_retriever,
        pattern_matcher=pattern_matcher,
        response_cache=response_cache,
        query_history=query_history
    )
    
    agent = CaculinhaBIAgent(
        llm=llm,
        code_gen_agent=code_gen_agent,
        field_mapper=field_mapper
    )
    
    prompt = "gere um grafico de ranking de vendas de todos os segmentos na une 2365"
    print(f"Executando prompt: '{prompt}'")
    
    try:
        # Executa o agente de forma assíncrona
        response = await agent.run_async(prompt)
        
        print("\n--- RESPOSTA DO AGENTE ---")
        print(json.dumps(response, indent=2, ensure_ascii=False) if isinstance(response, dict) else response)
        print("\n--------------------------")
        
        # Verifica sucesso
        if isinstance(response, dict) and response.get("type") == "code_result":
             print("SUCESSO: Gráfico gerado corretamente!")
             if response.get("chart_spec"):
                 print("DETALHE: chart_spec encontrado na resposta.")
        else:
             print("AVISO: A resposta não retornou um gráfico no formato esperado.")
             
    except Exception as e:
        print(f"\nErro durante a execução: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_graph_generation())
