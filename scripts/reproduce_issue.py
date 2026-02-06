
import requests
import json
import duckdb
import os
import sys

# 1. Setup
BASE_URL = "http://localhost:8000/api/v1"
PARQUET_FILE = "data/parquet/admmat.parquet"

def get_token():
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "demo123"})
        r.raise_for_status()
        return r.json()["access_token"]
    except Exception as e:
        print(f"[ERROR] Auth failed: {e}")
        sys.exit(1)

def count_ground_truth():
    """Conta quantas lojas REALMENTE têm vendas de tecidos > 0."""
    try:
        con = duckdb.connect()
        # Segmento 'TECIDOS' (case insensitive search)
        sql = f"""
            SELECT COUNT(DISTINCT UNE) as total_lojas
            FROM '{PARQUET_FILE}'
            WHERE NOMESEGMENTO ILIKE '%TECIDOS%'
            AND VENDA_30DD > 0
        """
        count = con.execute(sql).fetchone()[0]
        print(f"\n[GROUND TRUTH] Lojas com vendas de TECIDOS (>0): {count}")
        
        # Listar as lojas para inspeção visual
        sql_list = f"""
            SELECT DISTINCT UNE
            FROM '{PARQUET_FILE}'
            WHERE NOMESEGMENTO ILIKE '%TECIDOS%'
            AND VENDA_30DD > 0
            ORDER BY UNE
        """
        lojas = con.execute(sql_list).fetchall()
        print(f"[GROUND TRUTH] IDs das lojas: {[l[0] for l in lojas]}")
        return count
    except Exception as e:
        print(f"[ERROR] Database check failed: {e}")
        return 0

def test_agent_limit(token):
    """Testa o agente e captura os argumentos da ferramenta."""
    query = "como estao as vendas do segmento tecidos em todas as lojas"
    print(f"\n[AGENT TEST] Query: '{query}'")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"query": query, "session_id": "debug_limit_v2"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=90
        )
        data = resp.json()
        
        # Extrair tool calls
        tool_calls = data.get("full_agent_response", {}).get("tool_calls", [])
        
        if not tool_calls:
            print("[AGENT TEST] Nenhuma ferramenta chamada!")
            return

        for tc in tool_calls:
            fname = tc.get("function_name")
            args = tc.get("args", {})
            print(f"[AGENT TEST] Ferramenta: {fname}")
            print(f"[AGENT TEST] Argumentos: {json.dumps(args, indent=2)}")
            
            # Verificar limite especificamente
            limit_arg = args.get("limite")
            print(f"[AGENT TEST] Limite solicitado pelo LLM: {limit_arg} (Type: {type(limit_arg)})")

    except Exception as e:
        print(f"[ERROR] Agent test failed: {e}")

if __name__ == "__main__":
    print("--- INICIANDO DIAGNÓSTICO DE LIMITE ---")
    
    # 1. Ground Truth (Dados Reais)
    if os.path.exists(PARQUET_FILE):
        count_ground_truth()
    else:
        print(f"[WARN] Parquet not found at {PARQUET_FILE}, skipping ground truth check.")

    # 2. Agent Behavior (O que o LLM está pedindo?)
    token = get_token()
    test_agent_limit(token)
    print("\n--- FIM DO DIAGNÓSTICO ---")
