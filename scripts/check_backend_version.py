"""
Debug: Verificar se backend está usando versão corrigida
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

def check_backend_version():
    print("=== VERIFICANDO VERSÃO DO BACKEND ===\n")
    
    # 1. Verificar limite padrão
    print("1. Verificando limite padrão em flexible_query_tool...")
    from app.core.tools import flexible_query_tool
    import inspect
    
    tool = flexible_query_tool.consultar_dados_flexivel
    func = tool.func if hasattr(tool, 'func') else tool
    sig = inspect.signature(func)
    limite_param = sig.parameters['limite']
    
    if limite_param.default == 100:
        print(f"   ✅ Limite padrão: {limite_param.default} (CORRETO)")
    else:
        print(f"   ❌ Limite padrão: {limite_param.default} (ESPERADO: 100)")
    
    # 2. Verificar limite máximo
    print("\n2. Verificando limite máximo...")
    source = inspect.getsource(func)
    
    if "if limite > 500:" in source:
        print("   ✅ Limite máximo: 500 (CORRETO)")
    elif "if limite > 50:" in source:
        print("   ❌ Limite máximo: 50 (VERSÃO ANTIGA!)")
    else:
        print("   ⚠️ Limite máximo: NÃO ENCONTRADO")
    
    # 3. Verificar se backend precisa ser reiniciado
    print("\n3. Verificando se backend está rodando...")
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("   ✅ Backend está rodando")
            print("   ⚠️ ATENÇÃO: Se você fez alterações, REINICIE o backend!")
        else:
            print(f"   ⚠️ Backend respondeu com status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Backend NÃO está rodando")
        print("   Inicie com: python backend/main.py")
    except Exception as e:
        print(f"   ⚠️ Erro ao verificar backend: {e}")
    
    print("\n=== CONCLUSÃO ===")
    print("Se o backend está rodando, REINICIE para aplicar as correções:")
    print("  1. Pare o backend (Ctrl+C)")
    print("  2. python backend/main.py")

if __name__ == "__main__":
    check_backend_version()
