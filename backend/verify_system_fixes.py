
import requests
import json
import sseclient

BASE_URL = "http://127.0.0.1:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzYjc0NGRlYy05OGNhLTQ1ZDgtODNiOC03ODA5MGNlNGUxNTciLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiYWxsb3dlZF9zZWdtZW50cyI6WyIqIl0sImV4cCI6MTc2OTI5NDA5MSwidHlwZSI6ImFjY2VzcyJ9.YCkDDY_OT8kbntw--TksTEcGjUo5XCJdwK2KJ5h4qMA"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🔍 Iniciando Verificação de Correções (STRICT MODE)...\n")

# 1. Verificar Dashboard Executivo (DadosZerados Fix)
print("1️⃣ Testando Dashboard Executivo (Executive KPIs)...")
try:
    resp = requests.get(f"{BASE_URL}/dashboard/metrics/executive-kpis", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Dashboard Result: {json.dumps(data, indent=2)}")
        
        # Validar valores
        if data.get("vendas_total", 0) > 0:
            print("🎉 PASS: Vendas Totais > 0")
        else:
            print("❌ FAIL: Vendas Totais ainda está 0")
            exit(1)
    else:
        print(f"❌ FAIL: Erro HTTP {resp.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ EXCEPTION: {e}")
    exit(1)

print("\n------------------------------------------------\n")

import uuid
# ...
# 2. Verificar Chat Async (Co-routine Fix)
print("2️⃣ Testando Chat BI (Async Fix)...")
session_id = "testsession123"
print(f"   Session ID: {session_id}")

try:
    url = f"{BASE_URL}/chat/stream"
    params = {
        "q": "qual a previsão de vendas do produto 369947 para a une 35",
        "session_id": session_id,
        "token": TOKEN
    }
    
    resp = requests.get(url, params=params, stream=True, headers=headers)
    
    if resp.status_code == 200:
        print("✅ Conexão SSE estabelecida.")
        
        client = sseclient.SSEClient(resp)
        has_error = False
        events_received = 0
        
        for event in client.events():
            print(f"   📨 Evento: {event.event}")
            print(f"   📦 Data: {event.data}")
            
            if "Erro ao processar" in event.data or "AttributeError" in event.data or "'coroutine' object" in event.data:
                print("❌ FAIL: Erro detectado na resposta do Chat!")
                has_error = True
                break
                
            events_received += 1
            if events_received >= 3:
                break
        
        if not has_error:
            print("🎉 PASS: Chat respondeu sem erros de corrotina.")
        else:
            exit(1)
            
    else:
        print(f"❌ FAIL: Erro HTTP {resp.status_code}")
        exit(1)

except Exception as e:
    print(f"❌ EXCEPTION: {e}")
    exit(1)
