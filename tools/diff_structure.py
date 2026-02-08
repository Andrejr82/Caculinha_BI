#!/usr/bin/env python3
"""
diff_structure.py — Detecção de Arquivos Órfãos

Compara inventory_current.txt com allowed_structure.txt
Gera lista de arquivos fora da arquitetura oficial.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import re
from pathlib import Path
from datetime import datetime


def load_allowed_patterns(allowed_file: str) -> list[str]:
    """Carrega padrões permitidos do arquivo."""
    patterns = []
    
    with open(allowed_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ignora comentários e linhas vazias
            if not line or line.startswith('#'):
                continue
            patterns.append(line)
    
    return patterns


def is_allowed(file_path: str, patterns: list[str]) -> bool:
    """Verifica se o arquivo está na estrutura permitida."""
    file_path = file_path.replace('\\', '/')
    
    for pattern in patterns:
        pattern = pattern.replace('\\', '/')
        
        # Match exato
        if file_path == pattern:
            return True
        
        # Pattern é diretório (termina com /)
        if pattern.endswith('/'):
            if file_path.startswith(pattern):
                return True
        
        # Pattern começa com o caminho do arquivo
        if file_path.startswith(pattern.rstrip('/')):
            return True
    
    return False


def detect_orphans(inventory_file: str, allowed_file: str, output_file: str) -> int:
    """Detecta arquivos órfãos e gera relatório."""
    patterns = load_allowed_patterns(allowed_file)
    orphans = []
    
    with open(inventory_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ignora comentários e linhas vazias
            if not line or line.startswith('#'):
                continue
            
            if not is_allowed(line, patterns):
                orphans.append(line)
    
    # Gera relatório de órfãos
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Arquivos Órfãos — Fora da Arquitetura Oficial\n")
        f.write(f"# Gerado em: {datetime.now().isoformat()}\n")
        f.write(f"# Total de órfãos: {len(orphans)}\n")
        f.write("#" + "=" * 60 + "\n\n")
        
        # Agrupa por diretório para visualização
        current_dir = ""
        for orphan in sorted(orphans):
            dir_part = str(Path(orphan).parent)
            if dir_part != current_dir:
                current_dir = dir_part
                f.write(f"\n# {current_dir}/\n")
            f.write(f"{orphan}\n")
    
    return len(orphans)


if __name__ == "__main__":
    import sys
    
    inventory = sys.argv[1] if len(sys.argv) > 1 else "docs/inventory_current.txt"
    allowed = sys.argv[2] if len(sys.argv) > 2 else "docs/allowed_structure.txt"
    output = sys.argv[3] if len(sys.argv) > 3 else "docs/orphans.txt"
    
    count = detect_orphans(inventory, allowed, output)
    print(f"✅ Órfãos detectados: {output}")
    print(f"⚠️  Total de arquivos órfãos: {count}")
