
import os
import asyncio
import google.generativeai as genai
from google.generativeai.protos import Content, Part, FunctionCall, FunctionResponse
import dotenv

# Load .env
dotenv.load_dotenv("backend/.env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found")
    exit(1)

genai.configure(api_key=api_key)

async def test_empty_content():
    print("\n--- Test 1: Empty contents list ---")
    model = genai.GenerativeModel('gemini-3-flash-preview')
    try:
        response = model.generate_content(contents=[])
        print("Success (unexpected)")
    except Exception as e:
        print(f"Caught expected error: {e}")

async def test_empty_part_text():
    print("\n--- Test 2: Empty part text ---")
    model = genai.GenerativeModel('gemini-3-flash-preview')
    try:
        contents = [Content(role="user", parts=[Part(text="")])]
        response = model.generate_content(contents=contents)
        print("Success (unexpected)")
    except Exception as e:
        print(f"Caught error: {e}")

async def test_null_system_instruction():
    print("\n--- Test 3: Empty string system instruction ---")
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction="")
        response = model.generate_content(contents=[Content(role="user", parts=[Part(text="Hi")])])
        print("Success")
    except Exception as e:
        print(f"Caught error: {e}")

if __name__ == "__main__":
    asyncio.run(test_empty_content())
    asyncio.run(test_empty_part_text())
    asyncio.run(test_null_system_instruction())
