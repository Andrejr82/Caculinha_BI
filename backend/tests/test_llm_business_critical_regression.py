import json
from pathlib import Path

from backend.app.core.utils.executive_output import (
    classify_business_response_shape,
    ensure_executive_output,
    validate_executive_output,
)


def test_business_critical_dataset_keeps_executive_contract():
    dataset_path = Path("backend/tests/llmops/datasets/chatbi_business_critical_v2.json")
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))

    failures = []
    for case in payload.get("cases", []):
        query = str(case.get("query", ""))
        raw_response = str(case.get("raw_response", ""))
        expected_process = str(case.get("expected_process", ""))
        expected_template = str(case.get("expected_template", ""))

        formatted = ensure_executive_output(query=query, message=raw_response)
        checks = validate_executive_output(formatted)
        shape = classify_business_response_shape(query)

        missing = [name for name, ok in checks.items() if not ok]
        wrong_process = expected_process and shape["processo"] != expected_process
        wrong_template = expected_template and shape["template_id"] != expected_template

        if missing or wrong_process or wrong_template:
            failures.append(
                {
                    "id": case.get("id"),
                    "missing": missing,
                    "expected_process": expected_process,
                    "actual_process": shape["processo"],
                    "expected_template": expected_template,
                    "actual_template": shape["template_id"],
                }
            )

    assert failures == []


def test_promotion_query_receives_margin_oriented_operational_table():
    query = "vale fazer promocao da caneta bic sem destruir margem"
    formatted = ensure_executive_output(query=query, message="A promocao pode funcionar com disciplina de margem.")

    assert "| Indicador | Leitura |" in formatted
    assert "Margem/Preco" in formatted
    assert "limite mínimo de rentabilidade" in formatted


def test_rupture_query_receives_replenishment_action_language():
    query = "quais produtos estao em ruptura critica na papelaria"
    formatted = ensure_executive_output(query=query, message="Existem itens com risco imediato de perda de venda.")

    assert "Ruptura/Cobertura" in formatted
    assert "cobertura zerada ou abaixo de 3 dias" in formatted
    assert "reposição/transferência" in formatted
