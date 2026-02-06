"""
Script de teste para verificar funcionamento dos filtros de Analytics
"""
import requests
import json

# Configuração
BASE_URL = "http://localhost:8000/api/v1"
# Substitua com credenciais válidas
USERNAME = "admin@example.com"
PASSWORD = "admin123"

def test_filters():
    """Testa o novo sistema de filtros"""

    print("=" * 60)
    print("TESTE: Sistema de Filtros - Analytics")
    print("=" * 60)

    # 1. Login
    print("\n1. Fazendo login...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )

    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        print(login_response.text)
        return

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login bem-sucedido")

    # 2. Buscar opções de filtro
    print("\n2. Buscando opções de filtro...")
    filter_options_response = requests.get(
        f"{BASE_URL}/analytics/filter-options",
        headers=headers
    )

    if filter_options_response.status_code != 200:
        print(f"❌ Erro ao buscar opções: {filter_options_response.status_code}")
        print(filter_options_response.text)
        return

    options = filter_options_response.json()
    print("✅ Opções de filtro carregadas:")
    print(f"   Categorias disponíveis: {len(options['categorias'])}")
    if options['categorias']:
        print(f"   Exemplos: {options['categorias'][:3]}")
    print(f"   Segmentos disponíveis: {len(options['segmentos'])}")
    if options['segmentos']:
        print(f"   Exemplos: {options['segmentos'][:3]}")

    # 3. Testar análise sem filtros
    print("\n3. Testando análise sem filtros...")
    analysis_response = requests.get(
        f"{BASE_URL}/analytics/sales-analysis",
        headers=headers
    )

    if analysis_response.status_code != 200:
        print(f"❌ Erro na análise: {analysis_response.status_code}")
        print(analysis_response.text)
        return

    analysis = analysis_response.json()
    print("✅ Análise sem filtros:")
    print(f"   Categorias no gráfico: {len(analysis['vendas_por_categoria'])}")
    print(f"   Produtos com giro: {len(analysis['giro_estoque'])}")
    print(f"   Distribuição ABC: A={analysis['distribuicao_abc']['A']}, B={analysis['distribuicao_abc']['B']}, C={analysis['distribuicao_abc']['C']}")

    # 4. Testar com filtro de categoria
    if options['categorias']:
        categoria_teste = options['categorias'][0]
        print(f"\n4. Testando com filtro de categoria: '{categoria_teste}'...")

        filtered_response = requests.get(
            f"{BASE_URL}/analytics/sales-analysis",
            params={"categoria": categoria_teste},
            headers=headers
        )

        if filtered_response.status_code != 200:
            print(f"❌ Erro na análise filtrada: {filtered_response.status_code}")
            print(filtered_response.text)
            return

        filtered = filtered_response.json()
        print("✅ Análise com filtro de categoria:")
        print(f"   Categorias no gráfico: {len(filtered['vendas_por_categoria'])}")
        print(f"   Produtos com giro: {len(filtered['giro_estoque'])}")

    # 5. Testar com filtro de segmento
    if options['segmentos']:
        segmento_teste = options['segmentos'][0]
        print(f"\n5. Testando com filtro de segmento: '{segmento_teste}'...")

        filtered_response = requests.get(
            f"{BASE_URL}/analytics/sales-analysis",
            params={"segmento": segmento_teste},
            headers=headers
        )

        if filtered_response.status_code != 200:
            print(f"❌ Erro na análise filtrada: {filtered_response.status_code}")
            print(filtered_response.text)
            return

        filtered = filtered_response.json()
        print("✅ Análise com filtro de segmento:")
        print(f"   Categorias no gráfico: {len(filtered['vendas_por_categoria'])}")
        print(f"   Produtos com giro: {len(filtered['giro_estoque'])}")

    # 6. Testar com ambos os filtros
    if options['categorias'] and options['segmentos']:
        print(f"\n6. Testando com ambos os filtros...")

        filtered_response = requests.get(
            f"{BASE_URL}/analytics/sales-analysis",
            params={
                "categoria": options['categorias'][0],
                "segmento": options['segmentos'][0]
            },
            headers=headers
        )

        if filtered_response.status_code != 200:
            print(f"❌ Erro na análise filtrada: {filtered_response.status_code}")
            print(filtered_response.text)
            return

        filtered = filtered_response.json()
        print("✅ Análise com ambos os filtros:")
        print(f"   Categorias no gráfico: {len(filtered['vendas_por_categoria'])}")
        print(f"   Produtos com giro: {len(filtered['giro_estoque'])}")

    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_filters()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
