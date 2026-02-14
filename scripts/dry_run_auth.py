
import os
import sys
from pathlib import Path

# Adicionar root ao path
root = Path(__file__).parent.parent
sys.path.append(str(root))

print(f"--- AUTH DRY-RUN ---")
try:
    from backend.app.core.auth_service import auth_service
    print("[✅] AuthService imported successfully")
    
    # Testar inicialização de configuração
    from backend.app.config.settings import settings
    print(f"[✅] Settings loaded: SECRET_KEY={settings.SECRET_KEY[:5]}...")
    
    # Testar imports de segurança
    from backend.app.config.security import create_access_token
    print("[✅] Security functions imported")
    
    # Testar middleware imports
    from backend.app.api.middleware.auth import AuthMiddleware
    print("[✅] AuthMiddleware imported")

    print("\n[🚀] TENTANDO AUTENTICAÇÃO MOCK...")
    import asyncio
    
    async def run_test():
        # Vamos testar apenas o fluxo até o ponto que pode falhar
        try:
            # Isso deve falhar com credenciais erradas, mas não com NameError
            res = await auth_service.authenticate_user("test@test.com", "wrong")
            print(f"Resultado (esperado None): {res}")
        except NameError as ne:
            print(f"\n[❌] DETECTADO NAMEERROR: {ne}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"Outro erro (esperado): {type(e).__name__} - {e}")

    asyncio.run(run_test())

except NameError as ne:
    print(f"\n[❌] DETECTADO NAMEERROR NO IMPORT: {ne}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n[❌] ERRO GERAL: {type(e).__name__} - {e}")
    import traceback
    traceback.print_exc()
