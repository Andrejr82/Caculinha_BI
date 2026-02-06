"""
Teste focado no LLM para identificar o erro
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

async def test_llm():
    print("\n=== TESTE DO LLM (GROQ) ===\n")
    
    try:
        from app.core.llm_factory import LLMFactory
        from app.config.settings import settings
        
        print(f"LLM_PROVIDER configurado: {settings.LLM_PROVIDER}")
        print(f"LLM_MODEL_NAME configurado: {settings.LLM_MODEL_NAME}")
        print(f"GROQ_API_KEY presente: {bool(settings.GROQ_API_KEY)}")
        print(f"GOOGLE_API_KEY presente: {bool(settings.GOOGLE_API_KEY)}")
        
        print("\nCriando adapter Groq...")
        llm = LLMFactory.get_adapter(provider="groq", use_smart=True)
        print(f"Adapter criado: {type(llm).__name__}")
        
        print("\nTestando geracao de resposta...")
        response = await llm.generate_response("Responda apenas com a palavra: FUNCIONANDO")
        print(f"Resposta do LLM: {response}")
        
        print("\n[SUCESSO] LLM esta funcionando!")
        return True
        
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm())
    print(f"\nResultado: {'SUCESSO' if success else 'FALHA'}")
