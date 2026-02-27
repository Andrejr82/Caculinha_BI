import json

from backend.app.core.utils.context7 import clean_context7_violations
from backend.app.core.utils.response_sanitizer import clean_response_violations


def test_clean_response_violations_removes_plotly_json_block():
    payload = {
        "data": [{"x": [1, 2], "y": [3, 4]}],
        "layout": {"title": "Teste"},
    }
    text = f"Segue resultado técnico:\n```json\n{json.dumps(payload)}\n```"
    cleaned = clean_response_violations(text, context_type="chart")
    assert cleaned
    assert "data" not in cleaned.lower() or "layout" not in cleaned.lower()


def test_legacy_context7_alias_calls_new_sanitizer():
    raw = '{"data":[{"x":[1],"y":[2]}],"layout":{"title":"x"}}'
    new_clean = clean_response_violations(raw, context_type="chart")
    legacy_clean = clean_context7_violations(raw, context_type="chart")
    assert new_clean == legacy_clean
    assert "gráfico" in legacy_clean.lower() or "grafico" in legacy_clean.lower()

