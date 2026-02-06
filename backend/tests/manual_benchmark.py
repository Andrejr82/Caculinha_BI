import sys
import os
import asyncio
import time
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config.settings import settings
from app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from app.core.llm_gemini_adapter_v2 import GeminiLLMAdapterV2 as GeminiLLMAdapter
from app.core.utils.field_mapper import FieldMapper
from app.core.rag.query_retriever import QueryRetriever
from app.core.learning.pattern_matcher import PatternMatcher
from app.core.utils.response_cache import ResponseCache
from app.core.utils.query_history import QueryHistory
from app.core.agents.code_gen_agent import CodeGenAgent
from app.core.utils.session_manager import SessionManager

# Setup logging to console
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    print("=" * 60)
    print("🚀 INICIANDO BENCHMARK DO AGENTE BI")
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Initialization
    print("\n[1/3] Inicializando componentes...")
    start_init = time.time()
    
    if not settings.GEMINI_API_KEY:
        print("❌ ERRO: GEMINI_API_KEY não encontrada!")
        return

    try:
        # System instruction matches chat.py
        chatbi_system_instruction = """Você é o Assistente de BI da Caculinha...""" # Simplified for benchmark

        llm = GeminiLLMAdapter(
            model_name=settings.LLM_MODEL_NAME,
            gemini_api_key=settings.GEMINI_API_KEY,
            system_instruction="Você é um assistente de BI."
        ).get_llm()
        
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
        
        print(f"✅ Inicialização completa em {time.time() - start_init:.2f}s")
        
    except Exception as e:
        print(f"❌ Falha na inicialização: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Define Questions
    questions = [
        ("Básica", "Quantos produtos temos no segmento PAPELARIA?"),
        ("Média", "Qual o fabricante que mais vendeu nos últimos 30 dias?"),
        ("Complexa", "Compare as vendas entre a UNE 1 e a UNE 2365 para o segmento TECIDOS."),
        ("Gráfico", "Gere um gráfico de pizza dos top 5 fabricantes por estoque.")
    ]

    # 3. Run Benchmark
    print("\n[2/3] Executando perguntas...")
    
    results = []
    
    for category, query in questions:
        print(f"\n🔹 Teste: {category}")
        print(f"   Pergunta: '{query}'")
        
        start_query = time.time()
        try:
            # We use run_async if available or run wrapped in to_thread if not, 
            # but since we are in async main, let's try calling run directly if it's sync, 
            # or check if there is an async method. 
            # Looking at chat.py, there is run_async.
            
            response = await agent.run_async(user_query=query, chat_history=[])
            
            duration = time.time() - start_query
            
            # Analyze response
            has_chart = False
            has_table = False
            response_text = ""
            
            if isinstance(response, dict):
                response_type = response.get("type", "text")
                if response_type == "chart" or response.get("chart_spec"):
                    has_chart = True
                
                result_content = response.get("result", "")
                if isinstance(result_content, list):
                    has_table = True
                    response_text = f"Tabela com {len(result_content)} linhas"
                elif isinstance(result_content, dict):
                    response_text = str(result_content.get("mensagem", str(result_content)))
                else:
                    response_text = str(result_content)
            else:
                response_text = str(response)

            print(f"   ⏱️  Tempo: {duration:.2f}s")
            print(f"   📝 Resposta (resumo): {response_text[:100]}...")
            if has_chart:
                print("   📊 Gráfico gerado: SIM")
            if has_table:
                print("   📅 Tabela gerada: SIM")
                
            results.append({
                "category": category,
                "query": query,
                "duration": duration,
                "status": "OK",
                "chart": has_chart
            })
            
        except Exception as e:
            duration = time.time() - start_query
            print(f"   ❌ Erro: {e}")
            results.append({
                "category": category,
                "query": query,
                "duration": duration,
                "status": "ERROR",
                "error": str(e)
            })

    # 4. Summary
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS RESULTADOS")
    print("=" * 60)
    print(f"{ 'Categoria':<10} | {'Tempo (s)':<10} | {'Status':<10} | {'Gráfico'}")
    print("-" * 60)
    
    for r in results:
        print(f"{r['category']:<10} | {r['duration']:<10.2f} | {r['status']:<10} | {'✅' if r.get('chart') else '-'}")

if __name__ == "__main__":
    asyncio.run(main())
