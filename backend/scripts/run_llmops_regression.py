"""
Regression runner (Fase 3) para validar formato executivo do ChatBI.

Uso:
  python backend/scripts/run_llmops_regression.py
  python backend/scripts/run_llmops_regression.py --dataset backend/tests/llmops/datasets/chatbi_golden_v1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.utils.executive_output import ensure_executive_output, validate_executive_output
from backend.app.core.utils.report_templates import select_official_report_template


def run_regression(dataset_path: Path) -> int:
    if not dataset_path.exists():
        print(f"[ERRO] Dataset nao encontrado: {dataset_path}")
        return 2

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not isinstance(cases, list) or not cases:
        print("[ERRO] Dataset sem casos de teste.")
        return 2

    failures = []
    for case in cases:
        case_id = str(case.get("id", "unknown"))
        query = str(case.get("query", ""))
        raw_response = str(case.get("raw_response", ""))
        expected_process = str(case.get("expected_process", "")).strip().lower()

        formatted = ensure_executive_output(query=query, message=raw_response)
        checks = validate_executive_output(formatted)
        missing = [name for name, ok in checks.items() if not ok]

        selected = select_official_report_template(query)
        actual_process = str(selected.get("processo", "")).strip().lower()
        process_ok = not expected_process or expected_process == actual_process

        if missing or not process_ok:
            failures.append(
                {
                    "id": case_id,
                    "missing_sections": missing,
                    "expected_process": expected_process,
                    "actual_process": actual_process,
                }
            )
            continue

        print(f"[OK] {case_id}: secoes obrigatorias + template ({actual_process})")

    print(f"\nResumo: {len(cases) - len(failures)}/{len(cases)} casos aprovados")
    if failures:
        print("\nFalhas:")
        for item in failures:
            print(
                f"- {item['id']} | missing={item['missing_sections']} "
                f"| processo_esperado={item['expected_process']} processo_obtido={item['actual_process']}"
            )
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ChatBI Phase 3 LLMOps regression checks.")
    parser.add_argument(
        "--dataset",
        default="backend/tests/llmops/datasets/chatbi_golden_v1.json",
        help="Caminho para dataset versionado.",
    )
    args = parser.parse_args()
    return run_regression(Path(args.dataset))


if __name__ == "__main__":
    raise SystemExit(main())
