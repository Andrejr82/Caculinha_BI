#!/usr/bin/env python3
"""
quarantine_apply.py — Aplica Quarentena Controlada

Move itens classificados para quarentena ou legacy sem deletar.
Baseado na classification_matrix.md.

Autor: Debugger Agent
Data: 2026-02-07
"""

import shutil
from pathlib import Path
from datetime import datetime


# Configuração de movimentação
QUARANTINE_ITEMS = [
    # Testes archive
    "backend/tests/archive",
]

MOVE_TO_LEGACY_DOCS = [
    "backend/app/core/agents/DEPRECATED_README.md",
    "docs/DEBUG_REPORT.md",
    "docs/DEBUG_RESPOSTA_VAZIA.md",
]

REMOVE_ITEMS = [
    # Logs
    "backend/logs",
    "backend/backend_debug.log",
    "backend/debug_gemini.log",
    "backend/startup_error.log",
    "backend/std_err_fix.log",
    "backend/std_err_new.log",
    "backend/std_out_fix.log",
    "backend/std_out_new.log",
    "backend/test_results.log",
    "backend/verification.log",
    "backend/verification_2.log",
    "backend/verification_3.log",
    # Debug scripts
    "backend/scripts/debug_archive",
    # Session legada
    "backend/app/data/sessions/legacy.json",
    # Test outputs antigos
    "backend/test_db_report.html",
    "backend/test_db_results.txt",
    "backend/test_debug_output.txt",
    "backend/test_improved_output.txt",
    "backend/test_llm_raw_output.txt",
    "backend/test_output.txt",
    "backend/test_varejo_output.txt",
    "docs/archive/test_results.txt",
]


def move_to_quarantine(root: Path, log_file) -> int:
    """Move itens para legacy_quarantine/."""
    quarantine_dir = root / "legacy_quarantine"
    quarantine_dir.mkdir(exist_ok=True)
    
    count = 0
    for item_path in QUARANTINE_ITEMS:
        src = root / item_path
        if src.exists():
            dest = quarantine_dir / item_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            log_file.write(f"[QUARANTINE] {item_path} → legacy_quarantine/{item_path}\n")
            print(f"📦 QUARANTINE: {item_path}")
            count += 1
    
    return count


def move_to_legacy_docs(root: Path, log_file) -> int:
    """Move docs históricos para docs/legacy/."""
    legacy_dir = root / "docs" / "legacy"
    legacy_dir.mkdir(exist_ok=True)
    
    count = 0
    for item_path in MOVE_TO_LEGACY_DOCS:
        src = root / item_path
        if src.exists():
            dest = legacy_dir / Path(item_path).name
            shutil.move(str(src), str(dest))
            log_file.write(f"[LEGACY_DOCS] {item_path} → docs/legacy/{Path(item_path).name}\n")
            print(f"📄 LEGACY: {item_path}")
            count += 1
    
    return count


def remove_items(root: Path, log_file) -> int:
    """Remove itens classificados como REMOVE."""
    count = 0
    for item_path in REMOVE_ITEMS:
        src = root / item_path
        if src.exists():
            try:
                if src.is_dir():
                    shutil.rmtree(str(src))
                else:
                    src.unlink()
                log_file.write(f"[REMOVED] {item_path}\n")
                print(f"🗑️  REMOVED: {item_path}")
                count += 1
            except Exception as e:
                log_file.write(f"[ERROR] {item_path}: {e}\n")
                print(f"❌ ERROR: {item_path}: {e}")
    
    return count


def apply_quarantine(root_path: str, dry_run: bool = False) -> tuple[int, int, int]:
    """Aplica todas as operações de quarentena."""
    root = Path(root_path)
    
    log_path = root / "docs" / f"quarantine_log.md"
    
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("# Log de Quarentena\n\n")
        log.write(f"**Data:** {datetime.now().isoformat()}\n")
        log.write(f"**Dry Run:** {dry_run}\n\n")
        
        if dry_run:
            log.write("## Modo Simulação\n\n*Nenhuma alteração realizada.*\n\n")
            print("🔍 DRY RUN - Nenhuma alteração será feita")
            return 0, 0, 0
        
        log.write("## Operações Realizadas\n\n")
        
        # 1. Quarentena
        log.write("### Quarentena\n\n")
        q_count = move_to_quarantine(root, log)
        
        # 2. Legacy docs
        log.write("\n### Docs Legados\n\n")
        l_count = move_to_legacy_docs(root, log)
        
        # 3. Remoção
        log.write("\n### Remoção\n\n")
        r_count = remove_items(root, log)
        
        # Resumo
        log.write(f"\n## Resumo\n\n")
        log.write(f"- **Quarantinados:** {q_count}\n")
        log.write(f"- **Movidos para legacy:** {l_count}\n")
        log.write(f"- **Removidos:** {r_count}\n")
    
    return q_count, l_count, r_count


if __name__ == "__main__":
    import sys
    
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    dry_run = "--dry-run" in sys.argv
    
    q, l, r = apply_quarantine(root, dry_run)
    
    print(f"\n{'='*60}")
    print(f"✅ Quarentena aplicada:")
    print(f"   📦 Quarantinados: {q}")
    print(f"   📄 Movidos para legacy: {l}")
    print(f"   🗑️  Removidos: {r}")
    print(f"\n💾 Log salvo em docs/quarantine_log.md")
