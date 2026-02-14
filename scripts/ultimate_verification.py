
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def run_suite():
    print("=== CACULINHA BI ULTIMATE VERIFICATION ===\n")
    
    # 1. Health Check
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        if r.status_code == 200:
            print("[✅] 1. Backend Health: OK")
        else:
            print(f"[❌] 1. Backend Health: FAILED ({r.status_code})")
            return
    except Exception as e:
        print(f"[❌] 1. Backend Health: CONNECTION ERROR - {e}")
        return

    # 2. Login Check
    token = None
    try:
        payload = {"username": "user@agentbi.com", "password": "user123"}
        r = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token")
            print("[✅] 2. Auth Login: OK")
        else:
            print(f"[❌] 2. Auth Login: FAILED ({r.status_code}) - {r.text}")
            return
    except Exception as e:
        print(f"[❌] 2. Auth Login: ERROR - {e}")
        return

    # 3. Data Fetch Check (Rupturas)
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/rupturas/critical?limit=1", headers=headers, timeout=10)
        if r.status_code == 200:
            print("[✅] 3. Data Fetch (Rupturas): OK")
            data = r.json()
            if len(data) > 0:
                print(f"    - Sample: {data[0].get('NOME', 'Unknown Product')}")
            else:
                print("    - Warning: No data returned but endpoint is working.")
        else:
            print(f"[❌] 3. Data Fetch: FAILED ({r.status_code}) - {r.text}")
            return
    except Exception as e:
        print(f"[❌] 3. Data Fetch: ERROR - {e}")
        return

    print("\n[🎉] VERIFICAÇÃO CONCLUÍDA COM SUCESSO! SISTEMA 100% OPERACIONAL.")

if __name__ == "__main__":
    run_suite()
