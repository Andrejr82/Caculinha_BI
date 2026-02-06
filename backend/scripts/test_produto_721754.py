"""
Teste final com o produto específico do problema: 721754
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/dashboard"

print("="*80)
print("TESTE FINAL - PRODUTO 721754 (CANECA CRISTAL ECOLOGICO)")
print("="*80)

try:
    response = requests.post(
        f"{BASE_URL}/tools/prever_demanda_sazonal",
        json={
            "produto_id": "721754",
            "periodo_dias": 30,
            "considerar_sazonalidade": True
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ Resposta recebida com sucesso!")
        print(f"\nProduto: {data.get('nome', 'N/A')}")
        print(f"ID: {data.get('produto', 'N/A')}")
        
        seasonal_ctx = data.get('seasonal_context')
        
        print(f"\n{'='*80}")
        print("RESULTADO DA SAZONALIDADE:")
        print(f"{'='*80}")
        
        if seasonal_ctx:
            print(f"\n❌ PROBLEMA: Sazonalidade foi detectada (não deveria em Janeiro)")
            print(f"   Período: {seasonal_ctx.get('season', 'N/A').upper()}")
            print(f"   Multiplicador: {seasonal_ctx.get('multiplier', 'N/A')}x")
            print(f"   Segmento: {seasonal_ctx.get('produto_segmento', 'N/A')}")
            print(f"\n   Isso significa que a correção NÃO funcionou corretamente.")
        else:
            print(f"\n✅ SUCESSO: Nenhuma sazonalidade aplicada!")
            print(f"   Multiplicador: {data.get('multiplicador_aplicado', 'N/A')}")
            print(f"\n   ✅ A correção está funcionando corretamente!")
            print(f"   ✅ CASA E DECORAÇÃO não recebe mais alerta de VOLTA_AS_AULAS")
        
        print(f"\n{'='*80}")
        
    else:
        print(f"\n❌ Erro HTTP: {response.status_code}")
        print(f"Resposta: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n⚠️ Backend não está rodando em http://localhost:8000")
    print("   Por favor, inicie o backend com: python main.py")
except Exception as e:
    print(f"\n❌ Erro: {e}")

print("="*80)
