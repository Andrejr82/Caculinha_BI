"""
Runner da bateria de precisão operacional do ChatBI.

Uso:
  python backend/scripts/run_operational_precision_eval.py
  python backend/scripts/run_operational_precision_eval.py --dataset backend/tests/llmops/datasets/chatbi_operational_precision_v1.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.operational_precision_eval import evaluate_operational_precision_dataset


def run_eval(dataset_path: Path) -> int:
    if not dataset_path.exists():
        print(f"[ERRO] Dataset nao encontrado: {dataset_path}")
        return 2

    result = evaluate_operational_precision_dataset(dataset_path)
    total = int(result["total_cases"])
    passed = int(result["passed_cases"])
    failures = result["failures"]

    print(
        f"[RESUMO] Precisao operacional: {passed}/{total} casos aprovados "
        f"({result['pass_rate']:.0%})"
    )
    if failures:
        print("\nFalhas:")
        for item in failures:
            print(f"- {item['id']} ({item['kind']}): {item['failures']}")
        return 1

    print("[OK] Gate de precisao operacional aprovado.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ChatBI operational precision evaluation.")
    parser.add_argument(
        "--dataset",
        default="backend/tests/llmops/datasets/chatbi_operational_precision_v1.json",
        help="Caminho para dataset versionado de precisao operacional.",
    )
    args = parser.parse_args()
    return run_eval(Path(args.dataset))


if __name__ == "__main__":
    raise SystemExit(main())
