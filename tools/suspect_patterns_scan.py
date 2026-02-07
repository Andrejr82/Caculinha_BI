#!/usr/bin/env python3
"""
suspect_patterns_scan.py — Detecta Arquivos Suspeitos

Detecta padrões de arquivos legados, backups, dumps e lixo.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import re
from pathlib import Path
from datetime import datetime


# Padrões suspeitos
SUSPECT_EXTENSIONS = {
    '.bak', '.old', '.orig', '.tmp', '.dump', '.log',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.tgz',
    '.pyc', '.pyo', '.class', '.o', '.obj',
}

SUSPECT_PATTERNS = [
    r'repo_dump.*',
    r'backup.*',
    r'migrated.*',
    r'legacy.*',
    r'deprecated.*',
    r'old_.*',
    r'.*_old$',
    r'.*_backup$',
    r'.*_bak$',
    r'.*~$',
    r'.*\.orig$',
    r'copy.*',
    r'.*_copy$',
    r'teste?_.*',
    r'debug_.*',
    r'temp_.*',
    r'.*\.tmp$',
]

EXCLUDED_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    '.pytest_cache', '.mypy_cache', '.gemini'
}


def should_exclude(path: Path) -> bool:
    """Verifica se o caminho deve ser excluído."""
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


def is_suspect(file_path: Path) -> tuple[bool, str]:
    """Verifica se o arquivo é suspeito e retorna o motivo."""
    name = file_path.name.lower()
    ext = file_path.suffix.lower()
    
    # Extensão suspeita
    if ext in SUSPECT_EXTENSIONS:
        return True, f"extensão suspeita: {ext}"
    
    # Padrão de nome suspeito
    for pattern in SUSPECT_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return True, f"padrão: {pattern}"
    
    return False, ""


def scan_suspects(root_path: str) -> list[dict]:
    """Varre o repositório buscando arquivos suspeitos."""
    root = Path(root_path)
    suspects = []
    
    for item in root.rglob('*'):
        if item.is_file() and not should_exclude(item):
            is_susp, reason = is_suspect(item)
            if is_susp:
                try:
                    size = item.stat().st_size
                except:
                    size = 0
                
                suspects.append({
                    'path': str(item.relative_to(root)).replace('\\', '/'),
                    'reason': reason,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'extension': item.suffix.lower() or '(none)',
                })
    
    return sorted(suspects, key=lambda x: x['path'])


def save_markdown(suspects: list[dict], output_path: str):
    """Salva relatório em Markdown."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Arquivos Suspeitos Detectados\n\n")
        f.write(f"**Data:** {datetime.now().isoformat()}\n")
        f.write(f"**Total:** {len(suspects)}\n\n")
        
        # Agrupa por motivo
        by_reason = {}
        for s in suspects:
            reason = s['reason']
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(s)
        
        f.write("## Resumo por Motivo\n\n")
        f.write("| Motivo | Quantidade |\n")
        f.write("|--------|------------|\n")
        for reason, files in sorted(by_reason.items(), key=lambda x: len(x[1]), reverse=True):
            f.write(f"| {reason} | {len(files)} |\n")
        
        f.write("\n## Lista Completa\n\n")
        f.write("| Arquivo | Motivo | Tamanho (MB) |\n")
        f.write("|---------|--------|-------------|\n")
        for s in suspects:
            f.write(f"| `{s['path']}` | {s['reason']} | {s['size_mb']} |\n")
        
        if not suspects:
            f.write("*Nenhum arquivo suspeito encontrado.*\n")


if __name__ == "__main__":
    import sys
    
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print("🔍 Escaneando arquivos suspeitos...")
    suspects = scan_suspects(root)
    
    Path("docs").mkdir(exist_ok=True)
    save_markdown(suspects, "docs/suspects.md")
    
    print(f"✅ Relatório gerado: docs/suspects.md")
    print(f"   ⚠️  Arquivos suspeitos: {len(suspects)}")
