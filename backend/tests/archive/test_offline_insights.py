import asyncio
import sys
from app.config.settings import settings

# Force offline
settings.LLM_PROVIDER = "mock"

async def test_insights():
    print(f"🔧 TESTANDO INSIGHTS OFFLINE (Provider: {settings.LLM_PROVIDER})")
    
    # Importar a função interna (temos que importar o módulo, mas function é local)
    # Como a função está dentro do arquivo, mas não exportada, vamos importar o router ou simular
    # Melhor: vamos importar o modulo e chamar a funcao que criamos se ela for acessivel
    # Mas ela não é exportada.
    
    # Vamos fazer monkeypatch ou importar o endpoint handler e rodar
    # Mas o endpoint precisa de current_user (Depends).
    # Vamos mockar o user?
    
    try:
        from app.api.v1.endpoints.insights import _generate_offline_insights
        
        print("🚀 Executando _generate_offline_insights()...")
        insights = await _generate_offline_insights()
        
        print(f"✅ Gerados {len(insights)} insights:")
        for i in insights:
            print(f" - [{i['category'].upper()}] {i['title']}: {i['description']}")
            
        if len(insights) >= 3:
            print("🎉 Sucesso! Insights gerados com dados reais.")
        else:
            print("⚠️ Aviso: Menos insights que o esperado.")
            
    except ImportError:
        print("❌ Erro: Não conseguiu importar _generate_offline_insights. Verifique se foi definida no escopo do arquivo.")
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_insights())
