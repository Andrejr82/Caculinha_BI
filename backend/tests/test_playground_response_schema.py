from backend.app.core.playground_response_schema import enforce_playground_response_schema


def test_enforce_json_schema_from_partial_payload():
    content = '{"message":"ok"}'
    normalized = enforce_playground_response_schema(content, json_mode=True)
    assert '"summary"' in normalized
    assert '"table"' in normalized
    assert '"action"' in normalized


def test_enforce_text_schema_wraps_plain_text():
    normalized = enforce_playground_response_schema("Resposta simples", json_mode=False)
    assert "## Resumo" in normalized
    assert "## Tabela" in normalized
    assert "## Ação recomendada" in normalized
