"""
Teste com debug detalhado do erro
"""
import asyncio
import sys
import os
import traceback

sys.path.insert(0, os.path.abspath('.'))

async def test_with_debug():
    print("\n=== TESTE COM DEBUG DETALHADO ===\n")
    
    try:
        from app.services.llm_insights import LLMInsightsService
        
        print("[1/1] Chamando LLMInsightsService.generate_proactive_insights()...")
        
        try:
            insights = await LLMInsightsService.generate_proactive_insights()
            print(f"\n[OK] Retornou {len(insights)} insights")
            print(f"Tipo do retorno: {type(insights)}")
            
            if insights:
                print(f"\nPrimeiro insight:")
                print(f"  Tipo: {type(insights[0])}")
                print(f"  Conteudo: {insights[0]}")
            
            return True
            
        except TypeError as e:
            print(f"\n[ERRO TypeError] {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"\n[ERRO] {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_with_debug())
    print(f"\nResultado: {'SUCESSO' if success else 'FALHA'}")
