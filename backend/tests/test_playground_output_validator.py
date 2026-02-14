from backend.app.core.playground_output_validator import validate_playground_output


def test_validator_allows_read_only_sql():
    content = "```sql\nSELECT * FROM vendas WHERE data_venda >= '2026-01-01';\n```"
    result = validate_playground_output(content)
    assert result.is_safe is True
    assert result.detected_language == "sql"


def test_validator_blocks_destructive_sql():
    content = "```sql\nDROP TABLE vendas;\n```"
    result = validate_playground_output(content)
    assert result.is_safe is False
    assert "destrutivas" in result.reason.lower()


def test_validator_blocks_unsafe_python_calls():
    content = "```python\nimport os\nos.system('del *')\n```"
    result = validate_playground_output(content)
    assert result.is_safe is False
    assert result.detected_language == "python"
