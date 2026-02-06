#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste de startup - Verifica se todas as dependências estão OK
Execute: python test_startup.py
"""
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("[TESTE DE STARTUP] - Agent BI Backend")
print("=" * 60)
print()

# Test 1: Python Version
print("1. [OK] Python Version:")
print(f"   {sys.version}")
print()

# Test 2: Critical Imports
print("2. Testing Critical Imports...")
critical_imports = [
    ("fastapi", "FastAPI framework"),
    ("uvicorn", "ASGI server"),
    ("gunicorn", "WSGI server"),
    ("sqlalchemy", "Database ORM"),
    ("duckdb", "DuckDB engine"),
    ("google.generativeai", "Google Gemini AI"),
    ("groq", "Groq AI"),
    ("structlog", "Structured logging"),
    ("pydantic", "Data validation"),
    ("slowapi", "Rate limiting"),
    ("langchain", "LangChain framework"),
    ("plotly", "Chart generation"),
    ("pyarrow", "Parquet support"),
]

failed_imports = []
for module, description in critical_imports:
    try:
        __import__(module)
        print(f"   [OK] {module:30} - {description}")
    except ImportError as e:
        print(f"   [FAIL] {module:30} - ERROR: {e}")
        failed_imports.append(module)

print()

# Test 3: Environment Variables
print("3. Checking Critical Environment Variables...")
from dotenv import load_dotenv
load_dotenv()

env_vars = [
    ("SECRET_KEY", True),  # Required
    ("GROQ_API_KEY", False),  # Optional (or GEMINI_API_KEY)
    ("GEMINI_API_KEY", False),  # Optional (or GROQ_API_KEY)
    ("USE_SQL_SERVER", False),
    ("LLM_PROVIDER", False),
]

missing_required = []
for var, required in env_vars:
    value = os.getenv(var)
    if value:
        if "KEY" in var or "SECRET" in var:
            display = f"{value[:10]}..." if len(value) > 10 else "[REDACTED]"
        else:
            display = value
        print(f"   [OK] {var:20} = {display}")
    else:
        status = "[REQUIRED]" if required else "[Optional]"
        print(f"   {status} {var:20} = NOT SET")
        if required:
            missing_required.append(var)

print()

# Test 4: Check LLM Provider
llm_provider = os.getenv("LLM_PROVIDER", "groq")
groq_key = os.getenv("GROQ_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

print("4. LLM Provider Configuration:")
print(f"   Provider: {llm_provider}")
if llm_provider == "groq":
    if groq_key:
        print(f"   [OK] GROQ_API_KEY is set")
    else:
        print(f"   [FAIL] GROQ_API_KEY is MISSING (required for provider=groq)")
        missing_required.append("GROQ_API_KEY")
elif llm_provider == "google" or llm_provider == "gemini":
    if gemini_key:
        print(f"   [OK] GEMINI_API_KEY is set")
    else:
        print(f"   [FAIL] GEMINI_API_KEY is MISSING (required for provider=google)")
        missing_required.append("GEMINI_API_KEY")

print()

# Test 5: Parquet File
print("5. Checking Parquet Data File...")
parquet_path = os.getenv("PARQUET_FILE_PATH", "data/parquet/admmat.parquet")
full_path = os.path.join(os.path.dirname(__file__), "app", parquet_path.replace("data/", ""))

if os.path.exists(full_path):
    size_mb = os.path.getsize(full_path) / (1024 * 1024)
    print(f"   [OK] File exists: {full_path}")
    print(f"   [OK] Size: {size_mb:.2f} MB")
else:
    print(f"   [FAIL] File NOT FOUND: {full_path}")
    print(f"   Expected location: app/data/parquet/admmat.parquet")
    failed_imports.append("PARQUET_FILE")

print()

# Test 6: Try importing main app
print("6. Testing FastAPI App Import...")
try:
    # Add backend directory to path
    sys.path.insert(0, os.path.dirname(__file__))
    from main import app
    print(f"   [OK] FastAPI app imported successfully")
    print(f"   [OK] App title: {app.title}")
    print(f"   [OK] App version: {app.version}")
except Exception as e:
    print(f"   [FAIL] FAILED to import app: {e}")
    import traceback
    traceback.print_exc()
    failed_imports.append("MAIN_APP")

print()

# Summary
print("=" * 60)
print("📊 SUMMARY")
print("=" * 60)

if failed_imports or missing_required:
    print("[FAIL] STARTUP TEST FAILED")
    print()
    if failed_imports:
        print("Missing/Failed Imports:")
        for item in failed_imports:
            print(f"  - {item}")
    if missing_required:
        print()
        print("Missing Required Environment Variables:")
        for item in missing_required:
            print(f"  - {item}")
    print()
    print("[FIX] How to resolve:")
    if "GROQ_API_KEY" in missing_required or "GEMINI_API_KEY" in missing_required:
        print("  1. Get API key from https://console.groq.com/ (Groq - Free)")
        print("     OR https://aistudio.google.com/ (Gemini)")
        print("  2. Add to backend/.env file:")
        print("     GROQ_API_KEY=your_api_key_here")
    if "SECRET_KEY" in missing_required:
        print("  3. Generate SECRET_KEY (32+ chars):")
        print("     Add to backend/.env file:")
        print('     SECRET_KEY="your-secret-key-min-32-chars"')
    if failed_imports:
        print("  4. Install missing dependencies:")
        print("     pip install -r requirements.txt")

    sys.exit(1)
else:
    print("[SUCCESS] ALL TESTS PASSED")
    print()
    print("Backend is ready to start!")
    print()
    print("Start with:")
    print("  python main.py")
    print("  OR")
    print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print()
    sys.exit(0)
