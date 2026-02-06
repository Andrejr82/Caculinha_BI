def debug_env_content():
    try:
        with open(".env", "rb") as f:
            raw = f.read(50)
        print(f"Raw bytes start: {raw}")
        
        with open(".env", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        print(f"First 3 lines:")
        for i, line in enumerate(lines[:3]):
            print(f"{i}: {repr(line)}")
            
    except Exception as e:
        print(f"Error reading: {e}")

if __name__ == "__main__":
    debug_env_content()
