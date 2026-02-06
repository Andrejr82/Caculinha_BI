
import os
import sys
import logging
from pathlib import Path

# Adicionar o diretório backend ao sys.path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from app.core.llm_gemini_adapter_v3 import GeminiLLMAdapterV3
from app.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TEST_V3")

def test_v3_connection():
    print("\n=== Testando GeminiLLMAdapterV3 (Novo SDK) ===\n")
    
    if not settings.GEMINI_API_KEY:
        print("ERRO: GEMINI_API_KEY não encontrada no .env")
        return

    try:
        # Inicializar adaptador
        # Forçamos o modelo gemini-3-flash-preview para testar o thinking
        model_name = "gemini-3-flash-preview"
        adapter = GeminiLLMAdapterV3(model_name=model_name)
        
        prompt = "Explique brevemente por que o céu é azul. Use raciocínio passo a passo."
        messages = [{"role": "user", "content": prompt}]
        
        print(f"Enviando prompt para {model_name}...")
        result = adapter.get_completion(messages)
        
        if "error" in result:
            print(f"ERRO NA API: {result['error']}")
            return

        print("\n--- PENSAMENTO (THOUGHT) ---")
        if result.get("thought"):
            print(result["thought"])
        else:
            print("(Nenhum pensamento retornado ou não suportado pelo modelo)")

        print("\n--- RESPOSTA FINAL ---")
        print(result.get("content"))
        
        print("\n[SUCESSO] O novo adaptador V3 está operacional!")

    except Exception as e:
        print(f"FALHA CRÍTICA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_v3_connection()
