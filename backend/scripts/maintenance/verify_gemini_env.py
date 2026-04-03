import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega o .env explicitamente do diretório atual (backend)
load_dotenv(override=True)

# New SDK v1
try:
    from google import genai
    print("✅ google-genai SDK installed.")
except ImportError:
    print("❌ google-genai SDK NOT installed.")
    exit(1)

# Legacy SDK (Optional)
try:
    import google.generativeai as genai_legacy
    print("⚠️ google-generativeai installed (Legacy).")
except ImportError:
    print("ℹ️ google-generativeai NOT installed (Clean).")

from backend.app.config.settings import settings

def verify():
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        print("❌ GEMINI_API_KEY not found in settings/env.")
        exit(1)
        
    print(f"🔑 API Key found: {api_key[:5]}...{api_key[-3:]}")
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite", # Test with a cheap model
            contents="Say 'OK'"
        )
        print(f"✅ API Connection Successful: {response.text}")
    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
        exit(1)
