import asyncio
import google.generativeai as genai
import os
from app.config.settings import settings

def test_simple_genai():
    print("Testing basic Gemini generation (no tools)...")
    
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        print("❌ No API Key found.")
        return

    genai.configure(api_key=api_key)
    
    model_name = settings.LLM_MODEL_NAME
    print(f"Model: {model_name}")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, can you hear me?")
        print(f"✅ SUCCESS: {response.text}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    test_simple_genai()
