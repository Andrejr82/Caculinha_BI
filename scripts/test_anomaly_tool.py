import sys
import os
import json
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

# Setup logging
logging.basicConfig(level=logging.INFO)

from app.core.tools.anomaly_detection import analisar_anomalias

def test():
    print("--- Testing analisar_anomalias (Vendas por Loja) ---")
    # Z-Score de 1.0 para garantir que pegamos algum desvio no dataset de teste
    result = analisar_anomalias.invoke({
        "metrica": "VENDA_30DD",
        "dimensao": "UNE",
        "threshold": 1.0 
    })
    
    print("\n[RESULTADO DO AGENTE]")
    print(result.get("mensagem", "Sem mensagem"))
    
    if result.get("anomalias"):
        print("\n[DADOS TÉCNICOS]")
        print(f"Total de anomalias: {len(result['anomalias'])}")
        for a in result['anomalias'][:3]:
            print(f"- Loja {a.get('UNE')}: Valor {a.get('valor')}, Z-Score {a.get('z_score'):.2f}")

if __name__ == "__main__":
    test()
