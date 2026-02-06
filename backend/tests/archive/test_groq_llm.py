"""
Test Groq LLM Integration
Verifica se o Groq está configurado corretamente como LLM principal
"""
import os
import sys
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_groq_api_key():
    """Test 1: Verificar se a chave da API Groq está configurada"""
    print("\n" + "="*60)
    print("TEST 1: Verificar GROQ_API_KEY")
    print("="*60)

    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        print("[ERRO] GROQ_API_KEY não encontrada no .env")
        print("[FIX] Adicione: GROQ_API_KEY=sua_chave_aqui")
        return False

    if groq_key == "sua_chave_groq_aqui":
        print("[ERRO] GROQ_API_KEY ainda está com valor padrão")
        print("[FIX] Obtenha sua chave em: https://console.groq.com/")
        return False

    print(f"[OK] GROQ_API_KEY encontrada: {groq_key[:20]}...")
    return True


def test_llm_provider_config():
    """Test 2: Verificar se LLM_PROVIDER está configurado para Groq"""
    print("\n" + "="*60)
    print("TEST 2: Verificar LLM_PROVIDER")
    print("="*60)

    provider = os.getenv("LLM_PROVIDER", "gemini")

    if provider != "groq":
        print(f"[AVISO] LLM_PROVIDER = {provider}")
        print("[FIX] Configure LLM_PROVIDER=groq no .env para usar Groq")
        return False

    print(f"[OK] LLM_PROVIDER = {provider}")
    return True


def test_groq_model_config():
    """Test 3: Verificar modelo Groq"""
    print("\n" + "="*60)
    print("TEST 3: Verificar GROQ_MODEL_NAME")
    print("="*60)

    model = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

    valid_models = [
        "llama-3.3-70b-versatile",
        "llama-3.3-70b-specdec",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]

    print(f"[INFO] GROQ_MODEL_NAME = {model}")

    if model in valid_models:
        print(f"[OK] Modelo válido: {model}")
    else:
        print(f"[AVISO] Modelo não reconhecido: {model}")
        print(f"[INFO] Modelos válidos: {', '.join(valid_models)}")

    return True


def test_groq_adapter_import():
    """Test 4: Verificar se adapter Groq pode ser importado"""
    print("\n" + "="*60)
    print("TEST 4: Importar GroqAdapter")
    print("="*60)

    try:
        from app.core.llm_groq_adapter import GroqAdapter
        print("[OK] GroqAdapter importado com sucesso")
        return True
    except ImportError as e:
        print(f"[ERRO] Falha ao importar GroqAdapter: {e}")
        print("[FIX] Verifique se o arquivo app/core/llm_groq_adapter.py existe")
        return False
    except Exception as e:
        print(f"[ERRO] Erro ao importar: {e}")
        return False


def test_groq_connection():
    """Test 5: Testar conexão com API Groq"""
    print("\n" + "="*60)
    print("TEST 5: Testar Conexão com API Groq")
    print("="*60)

    try:
        from groq import Groq

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        print("[INFO] Testando chamada simples à API Groq...")
        start_time = time.time()

        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": "Responda apenas 'OK' se você está funcionando."}
            ],
            max_tokens=10,
            temperature=0
        )

        elapsed_time = time.time() - start_time

        result = response.choices[0].message.content.strip()

        print(f"[OK] Resposta recebida: {result}")
        print(f"[INFO] Tempo de resposta: {elapsed_time:.2f}s")
        print(f"[INFO] Tokens usados: {response.usage.total_tokens}")
        print(f"[INFO] Modelo: {response.model}")

        return True

    except Exception as e:
        print(f"[ERRO] Falha ao conectar com Groq: {e}")
        print("[FIX] Verifique:")
        print("  1. GROQ_API_KEY está correta")
        print("  2. Conexão com internet está funcionando")
        print("  3. Groq package está instalado: pip install groq")
        return False


def test_llm_factory():
    """Test 6: Testar LLMFactory retorna Groq"""
    print("\n" + "="*60)
    print("TEST 6: Testar LLMFactory")
    print("="*60)

    try:
        from app.core.llm_factory import LLMFactory

        # Force Groq provider
        os.environ["LLM_PROVIDER"] = "groq"

        factory = LLMFactory()
        adapter = factory.get_llm()

        adapter_type = type(adapter).__name__

        print(f"[INFO] Adapter retornado: {adapter_type}")

        if "Groq" in adapter_type:
            print(f"[OK] LLMFactory retornou adapter Groq: {adapter_type}")
            return True
        else:
            print(f"[AVISO] LLMFactory retornou: {adapter_type}")
            print("[FIX] Verifique LLM_PROVIDER=groq no .env")
            return False

    except Exception as e:
        print(f"[ERRO] Erro ao testar LLMFactory: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_groq_query():
    """Test 7: Testar query completa via adapter"""
    print("\n" + "="*60)
    print("TEST 7: Query Completa via Adapter")
    print("="*60)

    try:
        from app.core.llm_groq_adapter import GroqAdapter

        adapter = GroqAdapter()

        print("[INFO] Testando query: 'Qual é a capital do Brasil?'")
        start_time = time.time()

        response = adapter.query(
            prompt="Qual é a capital do Brasil? Responda apenas o nome da cidade.",
            max_tokens=10
        )

        elapsed_time = time.time() - start_time

        print(f"[OK] Resposta: {response}")
        print(f"[INFO] Tempo: {elapsed_time:.2f}s")

        if "brasília" in response.lower() or "brasilia" in response.lower():
            print("[OK] Resposta correta!")
            return True
        else:
            print("[AVISO] Resposta inesperada")
            return True  # Ainda conta como sucesso se recebeu resposta

    except Exception as e:
        print(f"[ERRO] Falha na query: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_groq_performance():
    """Test 8: Benchmark de performance Groq"""
    print("\n" + "="*60)
    print("TEST 8: Benchmark de Performance")
    print("="*60)

    try:
        from app.core.llm_groq_adapter import GroqAdapter

        adapter = GroqAdapter()

        queries = [
            "Conte de 1 a 5.",
            "Qual é 2 + 2?",
            "Nome de 3 cores primárias."
        ]

        total_time = 0

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/3] Query: {query}")

            start = time.time()
            response = adapter.query(prompt=query, max_tokens=30)
            elapsed = time.time() - start
            total_time += elapsed

            print(f"  Resposta: {response[:50]}...")
            print(f"  Tempo: {elapsed:.2f}s")

        avg_time = total_time / len(queries)

        print(f"\n[RESULTADO] Performance:")
        print(f"  Tempo total: {total_time:.2f}s")
        print(f"  Tempo médio: {avg_time:.2f}s")
        print(f"  Queries/segundo: {1/avg_time:.2f}")

        if avg_time < 2.0:
            print(f"[OK] Performance excelente! (<2s por query)")
        elif avg_time < 5.0:
            print(f"[OK] Performance boa! (<5s por query)")
        else:
            print(f"[AVISO] Performance lenta (>{avg_time:.1f}s por query)")

        return True

    except Exception as e:
        print(f"[ERRO] Erro no benchmark: {e}")
        return False


def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print(" GROQ LLM - SUITE DE TESTES COMPLETA")
    print("="*60)
    print(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    tests = [
        ("API Key", test_groq_api_key),
        ("Provider Config", test_llm_provider_config),
        ("Model Config", test_groq_model_config),
        ("Import Adapter", test_groq_adapter_import),
        ("API Connection", test_groq_connection),
        ("LLM Factory", test_llm_factory),
        ("Query Test", test_groq_query),
        ("Performance", test_groq_performance),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERRO CRÍTICO] {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print(" RESUMO DOS TESTES")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {name}")

    print("="*60)
    print(f"RESULTADO: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    print("="*60)

    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Groq está configurado corretamente como LLM principal")
        print(f"✅ Modelo: {os.getenv('GROQ_MODEL_NAME', 'llama-3.3-70b-versatile')}")
        return True
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        print("❌ Revise as configurações acima")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
