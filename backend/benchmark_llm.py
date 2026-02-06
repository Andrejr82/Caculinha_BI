
import os
import time
import json
import requests
from dotenv import load_dotenv

# Carregar chaves do .env
load_dotenv("backend/.env")

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
# Se voce nao tiver a chave da Groq no .env, pode colar aqui para o teste
GROQ_KEY = os.environ.get("GROQ_API_KEY", "SUA_CHAVE_GROQ_AQUI")

# Modelos para o teste
GEMINI_MODEL = "gemini-2.5-pro"
GROQ_MODEL = "llama-3.3-70b-versatile" # O melhor modelo gratuito da Groq hoje

PROMPT = """
Analise os seguintes dados de vendas de uma loja de tecidos:
- Tecido Algodão: 1.200m vendidos (Estoque: 50m)
- Linha Costura: 300 unidades vendidas (Estoque: 1.000m)
- Renda Guipir: 10m vendidos (Estoque: 500m)

Gere 3 insights rápidos de BI e uma recomendação de compra.
"""

def test_gemini():
    print(f"\n[Iniciando teste Gemini: {GEMINI_MODEL}]")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": PROMPT}]}]}
    
    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=30)
        end = time.time()
        
        if response.status_code == 200:
            data = response.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            print(f"✅ Sucesso! Tempo: {end - start:.2f}s")
            return text, end - start
        else:
            print(f"❌ Erro Gemini {response.status_code}: {response.text}")
            return None, 0
    except Exception as e:
        print(f"❌ Falha de conexão Gemini: {e}")
        return None, 0

def test_groq():
    if "SUA_CHAVE" in GROQ_KEY or not GROQ_KEY:
        print("\n[Aviso] Pulei o teste da Groq (Chave não configurada no .env ou no script)")
        return None, 0

    print(f"\n[Iniciando teste Groq: {GROQ_MODEL}]")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": PROMPT}]
    }
    
    start = time.time()
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        end = time.time()
        
        if response.status_code == 200:
            data = response.json()
            text = data['choices'][0]['message']['content']
            print(f"✅ Sucesso! Tempo: {end - start:.2f}s")
            return text, end - start
        else:
            print(f"❌ Erro Groq {response.status_code}: {response.text}")
            return None, 0
    except Exception as e:
        print(f"❌ Falha de conexão Groq: {e}")
        return None, 0

def run_benchmark():
    print("="*50)
    print("   BENCHMARK LLM: GOOGLE VS GROQ")
    print("="*50)
    
    g_text, g_time = test_gemini()
    q_text, q_time = test_groq()
    
    print("\n" + "="*50)
    print("   RESULTADO FINAL")
    print("="*50)
    if g_time: print(f"GOOGLE ({GEMINI_MODEL}): {g_time:.2f} segundos")
    if q_time: print(f"GROQ   ({GROQ_MODEL}): {q_time:.2f} segundos")
    
    if g_time and q_time:
        diff = ((g_time / q_time) - 1) * 100
        pref = "GROQ" if q_time < g_time else "GOOGLE"
        print(f"\nO {pref} foi {abs(diff):.1f}% mais rápido.")

if __name__ == "__main__":
    run_benchmark()
