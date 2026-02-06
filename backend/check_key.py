from app.config.settings import settings
import os

def check_key():
    print(f"DEBUG: settings._env_path = {settings._env_path}")
    print(f"DEBUG: Exists? {os.path.exists(settings._env_path)}")
    
    key = settings.GEMINI_API_KEY
    if not key:
        print("❌ No GEMINI_API_KEY found in settings.")
    else:
        visible = key[:5] + "..." + key[-4:] if len(key) > 10 else "Too short"
        print(f"✅ Loaded GEMINI_API_KEY: {visible}")
        print(f"   Length: {len(key)}")
        
    # Also check os.environ directly
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        visible_env = env_key[:5] + "..." + env_key[-4:]
        print(f"✅ OS Environment GEMINI_API_KEY: {visible_env}")
    else:
        print("ℹ️  GEMINI_API_KEY not in os.environ")

if __name__ == "__main__":
    check_key()
