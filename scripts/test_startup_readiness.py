
import os
import requests
import time
from pathlib import Path

def test_startup_readiness():
    print("--- STARTUP READINESS TEST ---")
    
    # 1. Arquivos de Dados
    parquet_path = Path("backend/data/parquet/admmat.parquet")
    if parquet_path.exists():
        print(f"[✅] Parquet Data: OK ({parquet_path.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print(f"[❌] Parquet Data: MISSING")

    # 2. Ambiente
    env_path = Path("backend/.env")
    if env_path.exists():
        print("[✅] .env file: OK")
    else:
        print("[❌] .env file: MISSING")

    # 3. Conectividade Local
    try:
        # Tenta verificar se o backend está rodando (opcional, pode ser falso se não iniciado ainda)
        r = requests.get("http://localhost:8000/health", timeout=2)
        print(f"[✅] Backend Health: OK ({r.status_code})")
    except:
        print("[ℹ️] Backend não detectado (esperado se não estiver rodando)")

    print("--- TEST CONCLUDED ---")

if __name__ == "__main__":
    test_startup_readiness()
