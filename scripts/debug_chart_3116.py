
import sys
import os
import time

# Adicionar raiz do projeto ao path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mock de variáveis de ambiente se necessário
os.environ["LLM_PROVIDER"] = "google" 

from backend.app.core.tools.universal_chart_generator import gerar_grafico_universal_v2

def test_chart_generation():
    print("--- Iniciando Teste de Geração de Gráfico (UNE 3116) ---")
    start_time = time.time()
    
    # Simula a chamada que o LLM deveria fazer
    # "gere um gráfico de ranking vendas dos segmentos da une 3116"
    try:
        # StructuredTool call requires .invoke with a dict
        result = gerar_grafico_universal_v2.invoke({
            "descricao": "ranking vendas une 3116",  # Removed "segmento"
            "filtro_une": "3116",
            "tipo_grafico": "bar",
            "limite": 10
        })
        
        elapsed = time.time() - start_time
        print(f"--- Fim do Teste ({elapsed:.2f} segundos) ---")
        
        if result.get("status") == "success":
            print("Status: SUCESSO")
            print(f"Dimensão: {result['summary']['dimensao']}")
            print(f"Métrica: {result['summary']['metrica']}")
            print(f"Total Itens: {result['summary']['total_itens']}")
            # print(f"Dados (primeiros 100 chars): {str(result['chart_data'])[:100]}...")
        else:
            print(f"Status: ERRO - {result.get('message')}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chart_generation()
