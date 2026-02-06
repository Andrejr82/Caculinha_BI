import os

def update_env():
    env_path = ".env"
    if not os.path.exists(env_path):
        print("Error: .env not found")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    updated = False
    
    for line in lines:
        if line.strip().startswith("LLM_PROVIDER"):
            new_lines.append('LLM_PROVIDER="google"\n')
            updated = True
            print("Updated LLM_PROVIDER to google")
        elif line.strip().startswith("LLM_MODEL_NAME"):
             new_lines.append('LLM_MODEL_NAME="gemini-1.5-flash"\n')
             print("Updated LLM_MODEL_NAME to gemini-1.5-flash")
        else:
            new_lines.append(line)
            
    if not updated:
        # If key didn't exist, append it
        new_lines.append('\nLLM_PROVIDER="google"\n')
        print("Appended LLM_PROVIDER=google")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print("✅ .env updated successfully.")

if __name__ == "__main__":
    update_env()
