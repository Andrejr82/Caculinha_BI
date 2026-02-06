"""
Script de teste de integração para validar a correção da sazonalidade
Testa os produtos específicos mencionados no problema
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1/dashboard"

def test_produto_papelaria():
    """
    Teste: Produto PAPEL CHAMEX (PAPELARIA) em Janeiro
    Esperado: Deve ter sazonalidade VOLTA_AS_AULAS
    """
    print("\n" + "="*80)
    print("TESTE 1: PAPEL CHAMEX A4 (PAPELARIA) - ID: 59294")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/tools/prever_demanda_sazonal",
        json={
            "produto_id": "59294",
            "periodo_dias": 30,
            "considerar_sazonalidade": True
        }
    )
    
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Produto: {data.get('nome', 'N/A')}")
    print(f"Seasonal Context: {data.get('seasonal_context')}")
    
    if data.get('seasonal_context'):
        ctx = data['seasonal_context']
        print(f"\n✅ SAZONALIDADE DETECTADA:")
        print(f"   - Período: {ctx.get('season', 'N/A').upper()}")
        print(f"   - Multiplicador: {ctx.get('multiplier', 'N/A')}x")
        print(f"   - Urgência: {ctx.get('urgency', 'N/A')}")
        print(f"   - Segmento: {ctx.get('produto_segmento', 'N/A')}")
        
        assert ctx['season'] == 'volta_as_aulas', "Deveria ser VOLTA_AS_AULAS"
        assert ctx['multiplier'] == 2.5, "Multiplicador deveria ser 2.5x"
        print("\n✅ TESTE PASSOU!")
    else:
        print("\n❌ ERRO: Sazonalidade NÃO foi detectada (deveria ter sido)")
        print(f"Multiplicador aplicado: {data.get('multiplicador_aplicado', 'N/A')}")
        assert False, "Sazonalidade deveria ter sido detectada para PAPELARIA em Janeiro"


def test_produto_casa_decoracao():
    """
    Teste: Produto CANECA CRISTAL (CASA E DECORAÇÃO) em Janeiro
    Esperado: NÃO deve ter sazonalidade VOLTA_AS_AULAS
    """
    print("\n" + "="*80)
    print("TESTE 2: CANECA CRISTAL ECOLOGICO (CASA E DECORAÇÃO) - ID: 721754")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/tools/prever_demanda_sazonal",
        json={
            "produto_id": "721754",
            "periodo_dias": 30,
            "considerar_sazonalidade": True
        }
    )
    
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Produto: {data.get('nome', 'N/A')}")
    print(f"Seasonal Context: {data.get('seasonal_context')}")
    
    if data.get('seasonal_context'):
        ctx = data['seasonal_context']
        print(f"\n❌ ERRO: SAZONALIDADE DETECTADA (não deveria):")
        print(f"   - Período: {ctx.get('season', 'N/A').upper()}")
        print(f"   - Multiplicador: {ctx.get('multiplier', 'N/A')}x")
        print(f"   - Segmento: {ctx.get('produto_segmento', 'N/A')}")
        
        # Se detectou volta_as_aulas para CASA E DECORAÇÃO, é um erro
        if ctx.get('season') == 'volta_as_aulas':
            assert False, "CASA E DECORAÇÃO NÃO deveria ter sazonalidade VOLTA_AS_AULAS"
    else:
        print("\n✅ CORRETO: Sazonalidade NÃO foi aplicada")
        print(f"Multiplicador aplicado: {data.get('multiplicador_aplicado', 1.0)}")
        assert data.get('multiplicador_aplicado', 1.0) == 1.0, "Multiplicador deveria ser 1.0"
        print("\n✅ TESTE PASSOU!")


def test_produto_casa_decoracao_natal():
    """
    Teste: Produto CANECA CRISTAL (CASA E DECORAÇÃO) em Dezembro
    Esperado: DEVE ter sazonalidade NATAL
    
    NOTA: Este teste só funciona se executado em dezembro
    """
    print("\n" + "="*80)
    print("TESTE 3: CANECA CRISTAL em Dezembro (deve ter NATAL)")
    print("="*80)
    
    mes_atual = datetime.now().month
    
    if mes_atual not in [11, 12]:
        print(f"⚠️ PULANDO: Teste só é válido em Nov/Dez (mês atual: {mes_atual})")
        return
    
    response = requests.post(
        f"{BASE_URL}/tools/prever_demanda_sazonal",
        json={
            "produto_id": "721754",
            "periodo_dias": 30,
            "considerar_sazonalidade": True
        }
    )
    
    data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Seasonal Context: {data.get('seasonal_context')}")
    
    if data.get('seasonal_context'):
        ctx = data['seasonal_context']
        print(f"\n✅ SAZONALIDADE DETECTADA:")
        print(f"   - Período: {ctx.get('season', 'N/A').upper()}")
        print(f"   - Multiplicador: {ctx.get('multiplier', 'N/A')}x")
        
        assert ctx['season'] == 'natal', "Deveria ser NATAL"
        print("\n✅ TESTE PASSOU!")
    else:
        print("\n❌ ERRO: Sazonalidade NÃO foi detectada (deveria ter NATAL)")
        assert False, "CASA E DECORAÇÃO deveria ter sazonalidade NATAL em Dezembro"


if __name__ == "__main__":
    print("\n🧪 INICIANDO TESTES DE INTEGRAÇÃO - CORREÇÃO DE SAZONALIDADE")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mês Atual: {datetime.now().month} ({datetime.now().strftime('%B')})")
    
    try:
        test_produto_papelaria()
        test_produto_casa_decoracao()
        test_produto_casa_decoracao_natal()
        
        print("\n" + "="*80)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*80)
        
    except AssertionError as e:
        print("\n" + "="*80)
        print(f"❌ TESTE FALHOU: {e}")
        print("="*80)
        raise
    except requests.exceptions.ConnectionError:
        print("\n" + "="*80)
        print("❌ ERRO: Não foi possível conectar ao backend")
        print("   Certifique-se de que o servidor está rodando em http://localhost:8000")
        print("="*80)
        raise
