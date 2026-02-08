#!/usr/bin/env python3
"""
audit_files.py — Inventário Completo do Repositório

Varre todo o repositório e gera lista de arquivos.
Exclui: .git, __pycache__, node_modules, .venv, venv

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import os
from pathlib import Path
from datetime import datetime


EXCLUDED_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    '.pytest_cache', '.mypy_cache', 'dist', 'build', '.next',
    'coverage', '.nyc_output', 'htmlcov', '.tox', 'eggs', '*.egg-info'
}

EXCLUDED_FILES = {
    '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.pyd'
}


def should_exclude(path: Path) -> bool:
    """Verifica se o caminho deve ser excluído."""
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
        if part.startswith('.') and part not in {'.agent', '.env', '.gitignore', '.env.example'}:
            if part not in {'.gemini'}:
                return True
    return False


def audit_repository(root_path: str) -> list[str]:
    """Varre o repositório e retorna lista de arquivos."""
    root = Path(root_path)
    files = []
    
    for item in root.rglob('*'):
        if item.is_file() and not should_exclude(item):
            rel_path = item.relative_to(root)
            files.append(str(rel_path).replace('\\', '/'))
    
    return sorted(files)


def generate_inventory(root_path: str, output_path: str) -> int:
    """Gera arquivo de inventário."""
    files = audit_repository(root_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Inventário do Repositório\n")
        f.write(f"# Gerado em: {datetime.now().isoformat()}\n")
        f.write(f"# Total de arquivos: {len(files)}\n")
        f.write(f"# Raiz: {root_path}\n")
        f.write("#" + "=" * 60 + "\n\n")
        
        for file_path in files:
            f.write(f"{file_path}\n")
    
    return len(files)


if __name__ == "__main__":
    import sys
    
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    output = sys.argv[2] if len(sys.argv) > 2 else "docs/inventory_current.txt"
    
    # Garante que a pasta docs existe
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    
    count = generate_inventory(root, output)
    print(f"✅ Inventário gerado: {output}")
    print(f"📁 Total de arquivos: {count}")
