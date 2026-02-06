import os
import sys
import json

# Adiciona o diretório backend ao path
backend_root = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_root)

# Carrega variáveis de ambiente
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_root, ".env"))

from app.core.tools.chart_tools import gerar_grafico_universal

def test_chart_tool():
    print("--- Testando gerar_grafico_universal ---")
    
    # Parâmetros baseados na tentativa do agente
    params = {
        "descricao": "ranking de vendas por segmento na une 2365",
        "filtros": {"UNE": 2365},
        "coluna_valor": "vendas",
        "coluna_agrupamento": "segmento",
        "limite": 10
    }
    
    try:
        # Chama a ferramenta diretamente
        # Nota: LangChain tools usam .invoke()
        result = gerar_grafico_universal.invoke(params)
        
        print("\n--- Resultado da Ferramenta ---")
        # Truncar chart_data para exibição
        if "chart_data" in result:
            chart_preview = result["chart_data"][:100] + "..."
            display_result = result.copy()
            display_result["chart_data"] = chart_preview
            print(json.dumps(display_result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        if result.get("status") == "success":
            print("\nSUCESSO: Ferramenta gerou o gráfico corretamente.")
        else:
            print("\nERRO: Ferramenta retornou erro.")
            
    except Exception as e:
        print(f"\nExceção durante a execução da ferramenta: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chart_tool()