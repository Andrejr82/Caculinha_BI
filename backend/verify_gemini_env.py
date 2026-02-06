import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega o .env explicitamente do diretório atual (backend)
load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("LLM_MODEL_NAME", "gemini-2.5-pro")

print(f"--- TESTE DE CONEXÃO GEMINI (.env) ---")
print(f"Modelo configurado: {model_name}")
print(f"Chave encontrada: {'Sim' if api_key else 'Não'}")

if api_key:
    # Mostra apenas o início e fim por segurança
    print(f"Chave (parcial): {api_key[:5]}...{api_key[-5:]}")
    
    genai.configure(api_key=api_key)
    try:
        print(f"Tentando gerar conteúdo com {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Olá, responda apenas 'CONEXAO_OK'")
        print(f"Resultado: {response.text}")
        print("\n✅ O Gemini está funcionando corretamente com as configurações do .env!")
    except Exception as e:
        print(f"\n❌ Falha na conexão: {str(e)}")
else:
    print("❌ Erro: GEMINI_API_KEY não encontrada no arquivo .env")
