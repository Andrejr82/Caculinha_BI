try:
    from dotenv import load_dotenv
    import os
    print("✅ python-dotenv is installed.")
    
    # Try loading
    load_dotenv(".env")
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        print(f"✅ Loaded key via dotenv: {key[:5]}...")
    else:
        print("❌ dotenv loaded but key not found in os.environ")
        
except ImportError:
    print("❌ python-dotenv NOT installed.")
