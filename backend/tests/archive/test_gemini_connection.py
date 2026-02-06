import os
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")

print(f"--- TESTE DE DIAGNÓSTICO FINAL ---")
print(f"Chave (parcial): {api_key[:5]}...{api_key[-5:]}")

genai.configure(api_key=api_key)

def test_model(name):
    print(f"\nTentando modelo: {name}...")
    try:
        model = genai.GenerativeModel(name)
        response = model.generate_content("Responda apenas 'OK'")
        print(f"✅ SUCESSO com {name}: {response.text}")
        return True
    except Exception as e:
        print(f"❌ ERRO com {name}: {str(e)}")
        return False

# Testar o modelo que você quer usar
test_model("gemini-3-flash-preview")

# Testar o modelo estável para ver se a chave funciona
print("\n--- Verificando se a chave é válida em modelo estável ---")
test_model("gemini-1.5-flash")