#!/usr/bin/env python3
"""
remove_confirmed.py — Remoção Definitiva Confirmada

Remove SOMENTE itens já validados na FASE 3.
Esta fase remove a pasta de quarentena após período de observação.

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

import shutil
from pathlib import Path
from datetime import datetime


# Itens para remoção definitiva (pós-validação)
CONFIRMED_REMOVALS = [
    # Quarentena antiga (após validação de que não quebra nada)
    # "legacy_quarantine",  # COMENTADO: Manter por segurança por enquanto
    
    # Arquivos de teste antigos na raiz do backend
    "backend/test_advanced_features.py",
    "backend/test_deep_knowledge.py",
    "backend/test_implementation.py",
    "backend/test_insights_complete.py",
    "backend/test_insights_debug.py",
    "backend/test_insights_detailed.py",
    "backend/test_llm_fixed.py",
    "backend/test_llm_improvements.py",
    "backend/test_llm_only.py",
    "backend/test_llm_raw.py",
    "backend/test_loop_detection.py",
    "backend/test_metrics_first.py",
    "backend/test_prompt_improvements.py",
    "backend/test_segment_filter.py",
    "backend/test_v3_validation.py",
]


def remove_confirmed(root_path: str, dry_run: bool = False) -> int:
    """Remove itens confirmados."""
    root = Path(root_path)
    removed = 0
    
    log_path = root / "docs" / "removal_log.md"
    
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("# Log de Remoção Definitiva\n\n")
        log.write(f"**Data:** {datetime.now().isoformat()}\n")
        log.write(f"**Dry Run:** {dry_run}\n\n")
        
        log.write("## Itens Removidos\n\n")
        
        for item_path in CONFIRMED_REMOVALS:
            src = root / item_path
            if src.exists():
                try:
                    if not dry_run:
                        if src.is_dir():
                            shutil.rmtree(str(src))
                        else:
                            src.unlink()
                    
                    log.write(f"- [x] `{item_path}`\n")
                    print(f"🗑️  REMOVED: {item_path}")
                    removed += 1
                except Exception as e:
                    log.write(f"- [ ] `{item_path}` (ERRO: {e})\n")
                    print(f"❌ ERROR: {item_path}: {e}")
            else:
                log.write(f"- [ ] `{item_path}` (não existe)\n")
        
        log.write(f"\n## Resumo\n\n")
        log.write(f"- **Removidos:** {removed}\n")
        log.write(f"- **Total previsto:** {len(CONFIRMED_REMOVALS)}\n")
    
    return removed


if __name__ == "__main__":
    import sys
    
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN - Simulando remoção\n")
    
    removed = remove_confirmed(root, dry_run)
    
    print(f"\n{'='*60}")
    print(f"✅ Remoção definitiva: {removed} arquivos")
    print(f"💾 Log salvo em docs/removal_log.md")
