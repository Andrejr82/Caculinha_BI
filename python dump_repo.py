import os

OUTPUT_FILE = "repo_dump.txt"

# Pastas que não devem ser varridas
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".idea",
    ".vscode"
}

# Extensões permitidas
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yml", ".yaml",
    ".md", ".txt",
    ".html", ".css",
    ".env", ".ini", ".cfg"
}

def is_allowed_file(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

def generate_dump(root_dir="."):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                if is_allowed_file(file):
                    file_path = os.path.join(root, file)

                    out.write("\n" + "="*120 + "\n")
                    out.write(f"FILE: {file_path}\n")
                    out.write("="*120 + "\n\n")

                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"[ERRO AO LER ARQUIVO]: {e}")

    print(f"\n✅ Dump gerado com sucesso: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dump()
