#!/usr/bin/env python3
"""
git_untracked_scan.py — Lista Arquivos Não-Trackeados

Lista arquivos que não estão no controle de versão.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import subprocess
from pathlib import Path
from datetime import datetime


def get_untracked_files(root_path: str) -> list[str]:
    """Lista arquivos não-trackeados via git status."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain', '-uall'],
            cwd=root_path,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        untracked = []
        for line in result.stdout.strip().split('\n'):
            if line.startswith('??'):
                # Remove prefixo '?? '
                file_path = line[3:].strip()
                untracked.append(file_path)
        
        return sorted(untracked)
    except Exception as e:
        print(f"❌ Erro ao executar git status: {e}")
        return []


def get_modified_files(root_path: str) -> list[tuple[str, str]]:
    """Lista arquivos modificados/adicionados/deletados."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=root_path,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        modified = []
        for line in result.stdout.strip().split('\n'):
            if not line or line.startswith('??'):
                continue
            status = line[:2].strip()
            file_path = line[3:].strip()
            modified.append((status, file_path))
        
        return sorted(modified, key=lambda x: x[1])
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


def save_markdown(untracked: list[str], modified: list[tuple[str, str]], output_path: str):
    """Salva relatório em Markdown."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Arquivos Não-Trackeados e Modificados\n\n")
        f.write(f"**Data:** {datetime.now().isoformat()}\n\n")
        
        # Status legend
        f.write("## Legenda de Status\n\n")
        f.write("| Status | Significado |\n")
        f.write("|--------|-------------|\n")
        f.write("| `??` | Não-trackeado (novo) |\n")
        f.write("| `M` | Modificado |\n")
        f.write("| `A` | Adicionado ao stage |\n")
        f.write("| `D` | Deletado |\n")
        f.write("| `R` | Renomeado |\n\n")
        
        # Untracked
        f.write(f"## Arquivos Não-Trackeados ({len(untracked)})\n\n")
        if untracked:
            f.write("| Arquivo |\n")
            f.write("|--------|\n")
            for file in untracked:
                f.write(f"| `{file}` |\n")
        else:
            f.write("*Nenhum arquivo não-trackeado.*\n")
        
        # Modified
        f.write(f"\n## Arquivos Modificados/Staged ({len(modified)})\n\n")
        if modified:
            f.write("| Status | Arquivo |\n")
            f.write("|--------|--------|\n")
            for status, file in modified:
                f.write(f"| `{status}` | `{file}` |\n")
        else:
            f.write("*Nenhum arquivo modificado.*\n")


if __name__ == "__main__":
    import sys
    
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print("🔍 Escaneando arquivos git...")
    untracked = get_untracked_files(root)
    modified = get_modified_files(root)
    
    Path("docs").mkdir(exist_ok=True)
    save_markdown(untracked, modified, "docs/untracked_files.md")
    
    print(f"✅ Relatório gerado: docs/untracked_files.md")
    print(f"   📁 Não-trackeados: {len(untracked)}")
    print(f"   📝 Modificados: {len(modified)}")
