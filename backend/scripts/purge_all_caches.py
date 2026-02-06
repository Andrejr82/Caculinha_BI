
import shutil
import os
import sys
from pathlib import Path

# Add backend root to path to import settings if needed, but for now we'll imply paths
BASE_DIR = Path(__file__).resolve().parent.parent # backend/

CACHE_DIRS = [
    BASE_DIR / "data" / "cache",
    BASE_DIR / "data" / "sessions",
    BASE_DIR / "app" / "services" / "__pycache__",
    BASE_DIR / "app" / "core" / "__pycache__",
    BASE_DIR / "app" / "infrastructure" / "__pycache__"
]

def purge_caches():
    print("🧹 Iniciando Limpeza Profunda de Cache...")
    
    deleted_count = 0
    reclaimed_space = 0
    
    for cache_dir in CACHE_DIRS:
        if cache_dir.exists():
            print(f"Processando: {cache_dir}")
            try:
                # Calculate size for report
                dir_size = sum(f.stat().st_size for f in cache_dir.glob('**/*') if f.is_file())
                reclaimed_space += dir_size
                
                # Delete
                shutil.rmtree(cache_dir)
                print(f"✅ {cache_dir.name} removido ({dir_size / 1024:.2f} KB)")
                deleted_count += 1
                
                # Recreate empty dir for data/cache to avoid startup errors
                if "data" in str(cache_dir):
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    print(f"   ↳ Diretório recriado vazio.")
                    
            except Exception as e:
                print(f"❌ Erro ao limpar {cache_dir}: {e}")
        else:
            print(f"ℹ️ {cache_dir.name} não encontrado (já limpo).")

    # Find all __pycache__ recursively
    print("\nProcurando __pycache__ residuais...")
    for pycache in BASE_DIR.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            print(f"✅ Removido: {pycache.relative_to(BASE_DIR)}")
            deleted_count += 1
        except Exception as e:
            pass

    print(f"\n✨ Limpeza Concluída!")
    print(f"Pastas removidas: {deleted_count}")
    print(f"Espaço recuperado: {reclaimed_space / 1024:.2f} KB")

if __name__ == "__main__":
    purge_caches()
