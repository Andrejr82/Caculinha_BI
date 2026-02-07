#!/usr/bin/env python3
"""
purge_orphans.py — Remoção Controlada de Arquivos Órfãos

Remove APENAS arquivos listados em docs/orphans.txt.
Loga cada remoção para auditoria.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


# Arquivos que devem ser MOVIDOS ao invés de removidos
PROTECTED_MOVES = {
    'data/parquet/admmat.parquet': 'backend/data/parquet/admmat.parquet',
    'data/parquet/users.parquet': 'backend/data/parquet/users.parquet',
}


def load_orphans(orphans_file: str) -> list[str]:
    """Carrega lista de órfãos."""
    orphans = []
    with open(orphans_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            orphans.append(line)
    return orphans


def purge_orphans(root_path: str, orphans_file: str, dry_run: bool = False) -> tuple[int, int, list[str]]:
    """
    Remove arquivos órfãos.
    
    Args:
        root_path: Raiz do repositório
        orphans_file: Arquivo com lista de órfãos
        dry_run: Se True, apenas simula a remoção
    
    Returns:
        (removidos, movidos, erros)
    """
    root = Path(root_path)
    orphans = load_orphans(orphans_file)
    
    removed = 0
    moved = 0
    errors = []
    
    log_file = root / "docs" / f"purge_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"# Purge Log\n")
        log.write(f"# Data: {datetime.now().isoformat()}\n")
        log.write(f"# Dry Run: {dry_run}\n")
        log.write("#" + "=" * 60 + "\n\n")
        
        for orphan in orphans:
            file_path = root / orphan.replace('/', os.sep)
            
            try:
                if orphan in PROTECTED_MOVES:
                    # Mover ao invés de remover
                    dest_path = root / PROTECTED_MOVES[orphan].replace('/', os.sep)
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if not dry_run:
                        shutil.move(str(file_path), str(dest_path))
                    
                    log.write(f"[MOVED] {orphan} → {PROTECTED_MOVES[orphan]}\n")
                    moved += 1
                    print(f"📦 MOVED: {orphan} → {PROTECTED_MOVES[orphan]}")
                
                elif file_path.exists():
                    if not dry_run:
                        file_path.unlink()
                    
                    log.write(f"[REMOVED] {orphan}\n")
                    removed += 1
                    print(f"🗑️  REMOVED: {orphan}")
                
                else:
                    log.write(f"[SKIP] {orphan} (não existe)\n")
            
            except Exception as e:
                error_msg = f"{orphan}: {str(e)}"
                errors.append(error_msg)
                log.write(f"[ERROR] {error_msg}\n")
                print(f"❌ ERROR: {error_msg}")
        
        # Remove diretórios vazios
        log.write("\n# Limpeza de diretórios vazios\n")
        for orphan in orphans:
            dir_path = (root / orphan.replace('/', os.sep)).parent
            try:
                while dir_path != root and dir_path.exists():
                    if not any(dir_path.iterdir()):
                        if not dry_run:
                            dir_path.rmdir()
                        log.write(f"[RMDIR] {dir_path.relative_to(root)}\n")
                        print(f"📁 RMDIR: {dir_path.relative_to(root)}")
                        dir_path = dir_path.parent
                    else:
                        break
            except Exception:
                pass
        
        log.write(f"\n# RESUMO\n")
        log.write(f"# Removidos: {removed}\n")
        log.write(f"# Movidos: {moved}\n")
        log.write(f"# Erros: {len(errors)}\n")
    
    return removed, moved, errors


if __name__ == "__main__":
    import sys
    
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    orphans_file = sys.argv[2] if len(sys.argv) > 2 else "docs/orphans.txt"
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN - Nenhum arquivo será removido\n")
    
    removed, moved, errors = purge_orphans(root, orphans_file, dry_run)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Removidos: {removed}")
    print(f"📦 Movidos: {moved}")
    print(f"❌ Erros: {len(errors)}")
    
    if not dry_run:
        print(f"\n💾 Log salvo em docs/purge_log_*.txt")
