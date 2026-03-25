import json
from pathlib import Path

from backend.app.core.operational_precision_eval import evaluate_operational_precision_dataset


def test_operational_precision_gate_meets_required_threshold():
    dataset_path = Path("backend/tests/llmops/datasets/chatbi_operational_precision_v1.json")
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    expected_total = len(payload.get("cases", []))

    result = evaluate_operational_precision_dataset(dataset_path)

    assert result["total_cases"] == expected_total
    assert result["pass_rate"] == 1.0, result["failures"]
    assert result["failures"] == []
