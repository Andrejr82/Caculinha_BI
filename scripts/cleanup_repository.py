"""
Script de Limpeza do Repositório Git
Resolve problemas de lock e remove arquivos desnecessários do tracking

Execução: python scripts/cleanup_repository.py
"""

import os
import subprocess
import shutil
import sys
import time

# Diretório do projeto
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_cmd(cmd, ignore_errors=False):
    """Executa comando e retorna resultado"""
    print(f"  > {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=PROJECT_DIR
        )
        if result.returncode != 0 and not ignore_errors:
            print(f"    WARN: {result.stderr[:200]}")
        return result.returncode == 0
    except Exception as e:
        print(f"    ERROR: {e}")
        return False

def kill_git_processes():
    """Mata todos os processos Git"""
    print("\n🔸 Matando processos Git...")
    run_cmd("taskkill /F /IM git.exe", ignore_errors=True)
    time.sleep(2)

def remove_git_locks():
    """Remove arquivos de lock do Git"""
    print("\n🔸 Removendo locks...")
    git_dir = os.path.join(PROJECT_DIR, ".git")
    
    lock_files = [
        os.path.join(git_dir, "index.lock"),
        os.path.join(git_dir, "HEAD.lock"),
        os.path.join(git_dir, "config.lock"),
    ]
    
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"    Removido: {lock_file}")
            except Exception as e:
                print(f"    ERRO ao remover {lock_file}: {e}")

def update_gitignore():
    """Garante que .gitignore tem as entradas corretas"""
    print("\n🔸 Atualizando .gitignore...")
    gitignore_path = os.path.join(PROJECT_DIR, ".gitignore")
    
    required_entries = [
        "# Node modules (NÃO rastrear)",
        "frontend-solid/node_modules/",
        "**/node_modules/",
        "",
        "# Arquivos temporários",
        "*.lock",
        "*.tmp",
        "",
        "# Cache Python",
        "__pycache__/",
        "*.pyc",
        "backend/__pycache__/",
        "backend/**/__pycache__/",
    ]
    
    with open(gitignore_path, "r", encoding="utf-8") as f:
        current = f.read()
    
    # Adicionar entradas que faltam
    additions = []
    for entry in required_entries:
        if entry and entry not in current:
            additions.append(entry)
    
    if additions:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n# === Adicionado por cleanup_repository.py ===\n")
            for entry in additions:
                f.write(entry + "\n")
        print(f"    Adicionadas {len(additions)} entradas")
    else:
        print("    .gitignore já está atualizado")

def untrack_node_modules():
    """Remove node_modules do tracking sem deletar arquivos"""
    print("\n🔸 Removendo node_modules do tracking...")
    
    # Remover do cache (--cached = não deleta arquivos)
    run_cmd("git rm -r --cached frontend-solid/node_modules/ 2>$null", ignore_errors=True)
    run_cmd("git rm -r --cached node_modules/ 2>$null", ignore_errors=True)

def untrack_pycache():
    """Remove __pycache__ do tracking"""
    print("\n🔸 Removendo __pycache__ do tracking...")
    run_cmd("git rm -r --cached **/__pycache__/ 2>$null", ignore_errors=True)
    run_cmd("git rm -r --cached backend/**/__pycache__/ 2>$null", ignore_errors=True)

def reset_git_index():
    """Reseta o índice do Git"""
    print("\n🔸 Resetando índice do Git...")
    run_cmd("git reset")

def show_status():
    """Mostra status atual"""
    print("\n🔸 Status do repositório:")
    run_cmd("git status --short | head -20")

def create_commit():
    """Cria commit com as mudanças"""
    print("\n🔸 Preparando commit...")
    
    # Adicionar apenas arquivos importantes
    files_to_add = [
        "backend/app/core/agents/caculinha_bi_agent.py",
        "backend/app/core/tools/flexible_query_tool.py",
        "backend/app/core/llm_factory.py",
        "backend/app/core/prompts/master_prompt.py",
        "backend/prompts/",
        "backend/utils/",
        "backend/tools/gemini_tools.py",
        "backend/test_implementation.py",
        ".gitignore",
    ]
    
    for f in files_to_add:
        run_cmd(f"git add {f}", ignore_errors=True)
    
    # Commit
    run_cmd('git commit -m "fix: correcoes BI Solution + limpeza repositorio"')

def main():
    print("=" * 60)
    print("🧹 LIMPEZA DO REPOSITÓRIO GIT - BI Solution")
    print("=" * 60)
    
    os.chdir(PROJECT_DIR)
    
    # 1. Matar processos Git
    kill_git_processes()
    
    # 2. Remover locks
    remove_git_locks()
    
    # 3. Atualizar .gitignore
    update_gitignore()
    
    # 4. Remover node_modules do tracking
    untrack_node_modules()
    
    # 5. Remover __pycache__ do tracking
    untrack_pycache()
    
    # 6. Reset index
    reset_git_index()
    
    # 7. Status
    show_status()
    
    # 8. Perguntar se quer fazer commit
    print("\n" + "=" * 60)
    print("✅ LIMPEZA CONCLUÍDA!")
    print("=" * 60)
    print("\nAgora execute manualmente:")
    print("  git add .")
    print('  git commit -m "fix: correcoes BI Solution"')
    print("  git push origin main")

if __name__ == "__main__":
    main()
