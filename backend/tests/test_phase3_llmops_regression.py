import json
from pathlib import Path

from backend.app.core.utils.executive_output import ensure_executive_output, validate_executive_output
from backend.app.core.utils.report_templates import get_official_report_templates, select_official_report_template


def test_official_templates_catalog_available():
    templates = get_official_report_templates()
    assert isinstance(templates, list)
    assert len(templates) >= 6
    assert all("id" in t and "processo" in t and "nome" in t for t in templates)


def test_business_response_is_forced_to_phase3_executive_format():
    query = "quero um resumo de vendas por segmento"
    raw = "As vendas cresceram no periodo analisado."
    formatted = ensure_executive_output(query=query, message=raw)
    checks = validate_executive_output(formatted)
    assert all(checks.values())


def test_golden_dataset_phase3_regression_contract():
    dataset_path = Path("backend/tests/llmops/datasets/chatbi_golden_v1.json")
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))

    failures = []
    for case in payload.get("cases", []):
        query = str(case.get("query", ""))
        raw_response = str(case.get("raw_response", ""))
        expected_process = str(case.get("expected_process", "")).strip().lower()

        formatted = ensure_executive_output(query=query, message=raw_response)
        checks = validate_executive_output(formatted)
        missing = [name for name, ok in checks.items() if not ok]

        selected = select_official_report_template(query)
        actual_process = str(selected.get("processo", "")).strip().lower()
        process_ok = not expected_process or actual_process == expected_process

        if missing or not process_ok:
            failures.append(
                {
                    "id": case.get("id"),
                    "missing": missing,
                    "expected_process": expected_process,
                    "actual_process": actual_process,
                }
            )

    assert failures == []
