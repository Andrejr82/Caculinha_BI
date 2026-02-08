#!/usr/bin/env python3
"""
deep_inventory.py — Inventário Profundo do Repositório

Varre todos arquivos e diretórios coletando:
- Caminho, tamanho, extensão, última modificação
- Identifica arquivos grandes (>= 50MB) e suspeitos

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import os
import csv
from pathlib import Path
from datetime import datetime


EXCLUDED_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    '.pytest_cache', '.mypy_cache', 'dist', 'build', '.next',
    'coverage', '.nyc_output', 'htmlcov', '.tox', 'eggs',
    'test-results', '.gemini'
}

LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 50MB


def should_exclude(path: Path) -> bool:
    """Verifica se o caminho deve ser excluído."""
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


def get_file_info(file_path: Path, root: Path) -> dict:
    """Coleta informações de um arquivo."""
    try:
        stat = file_path.stat()
        rel_path = file_path.relative_to(root)
        return {
            'path': str(rel_path).replace('\\', '/'),
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'extension': file_path.suffix.lower() or '(none)',
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'is_large': stat.st_size >= LARGE_FILE_THRESHOLD,
        }
    except Exception as e:
        return {
            'path': str(file_path.relative_to(root)).replace('\\', '/'),
            'error': str(e)
        }


def deep_inventory(root_path: str) -> tuple[list[dict], list[dict]]:
    """Varre o repositório e retorna inventário completo."""
    root = Path(root_path)
    all_files = []
    large_files = []
    
    for item in root.rglob('*'):
        if item.is_file() and not should_exclude(item):
            info = get_file_info(item, root)
            all_files.append(info)
            if info.get('is_large'):
                large_files.append(info)
    
    # Ordena por caminho
    all_files.sort(key=lambda x: x.get('path', ''))
    large_files.sort(key=lambda x: x.get('size_bytes', 0), reverse=True)
    
    return all_files, large_files


def save_csv(files: list[dict], output_path: str):
    """Salva inventário em CSV."""
    if not files:
        return
    
    fieldnames = ['path', 'size_bytes', 'size_mb', 'extension', 'modified', 'is_large']
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(files)


def save_markdown(files: list[dict], large_files: list[dict], output_path: str):
    """Salva inventário em Markdown."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Inventário Completo do Repositório\n\n")
        f.write(f"**Data:** {datetime.now().isoformat()}\n")
        f.write(f"**Total de arquivos:** {len(files)}\n")
        f.write(f"**Arquivos grandes (>50MB):** {len(large_files)}\n\n")
        
        # Estatísticas por extensão
        ext_stats = {}
        for file in files:
            ext = file.get('extension', '(none)')
            if ext not in ext_stats:
                ext_stats[ext] = {'count': 0, 'size': 0}
            ext_stats[ext]['count'] += 1
            ext_stats[ext]['size'] += file.get('size_bytes', 0)
        
        f.write("## Estatísticas por Extensão\n\n")
        f.write("| Extensão | Arquivos | Tamanho Total (MB) |\n")
        f.write("|----------|----------|--------------------|\n")
        for ext, stats in sorted(ext_stats.items(), key=lambda x: x[1]['size'], reverse=True)[:20]:
            f.write(f"| {ext} | {stats['count']} | {round(stats['size']/(1024*1024), 2)} |\n")
        
        # Arquivos grandes
        if large_files:
            f.write("\n## Arquivos Grandes (>50MB)\n\n")
            f.write("| Arquivo | Tamanho (MB) |\n")
            f.write("|---------|-------------|\n")
            for file in large_files:
                f.write(f"| `{file['path']}` | {file['size_mb']} |\n")
        
        # Lista completa (primeiros 200)
        f.write("\n## Lista de Arquivos (primeiros 200)\n\n")
        f.write("| Arquivo | Tamanho (MB) | Extensão |\n")
        f.write("|---------|-------------|----------|\n")
        for file in files[:200]:
            f.write(f"| `{file['path']}` | {file.get('size_mb', 0)} | {file.get('extension', '')} |\n")
        
        if len(files) > 200:
            f.write(f"\n*... e mais {len(files) - 200} arquivos. Veja inventory_full.csv para lista completa.*\n")


if __name__ == "__main__":
    import sys
    
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print("🔍 Varrendo repositório...")
    all_files, large_files = deep_inventory(root)
    
    # Garante que docs existe
    Path("docs").mkdir(exist_ok=True)
    
    save_csv(all_files, "docs/inventory_full.csv")
    save_markdown(all_files, large_files, "docs/inventory_full.md")
    
    print(f"✅ Inventário gerado:")
    print(f"   📄 docs/inventory_full.csv")
    print(f"   📄 docs/inventory_full.md")
    print(f"   📁 Total de arquivos: {len(all_files)}")
    print(f"   ⚠️  Arquivos grandes: {len(large_files)}")
