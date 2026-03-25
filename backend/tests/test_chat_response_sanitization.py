from backend.app.api.v1.endpoints.chat import _sanitize_response_for_role


def test_sanitize_response_for_role_restricts_internal_sections_for_user():
    raw = (
        "## Resumo executivo\n"
        "- Total de vendas por UNE consolidado com sucesso. UNE líder: 1685.\n"
        "- Template oficial: Performance de Vendas (comercial)\n\n"
        "## Tabela operacional\n"
        "| Loja (UNE) | Venda (R$) |\n"
        "|---|---|\n"
        "| 1685 | 10.000,00 |\n\n"
        "## SQL/Python\n"
        "```sql\nSELECT * FROM admmat LIMIT 50;\n```\n\n"
        "## Recorte e evidência\n"
        "- Métrica: soma de vendas por UNE."
    )

    sanitized = _sanitize_response_for_role(raw, "user")

    assert "Detalhamento por loja/UNE restrito para este perfil." in sanitized
    assert "SQL/Python" not in sanitized
    assert "SELECT * FROM admmat" not in sanitized
    assert "Template oficial" not in sanitized
    assert "UNE lider: [restrito]" in sanitized


def test_sanitize_response_for_role_keeps_detail_for_admin():
    raw = (
        "## Tabela operacional\n"
        "| Loja (UNE) | Venda (R$) |\n"
        "|---|---|\n"
        "| 1685 | 10.000,00 |\n\n"
        "## SQL/Python\n"
        "```sql\nSELECT * FROM admmat LIMIT 50;\n```"
    )

    sanitized = _sanitize_response_for_role(raw, "admin")

    assert "| Loja (UNE) | Venda (R$) |" in sanitized
    assert "SQL/Python" not in sanitized
    assert "SELECT * FROM admmat LIMIT 50;" not in sanitized


def test_sanitize_response_for_role_removes_active_html_payloads():
    raw = (
        "Resumo com link suspeito <a href=\"javascript:alert(1)\" onclick=\"alert(2)\">clique</a>\n"
        "<script>alert('xss')</script>"
    )

    sanitized = _sanitize_response_for_role(raw, "admin")

    assert "javascript:" not in sanitized.lower()
    assert "onclick" not in sanitized.lower()
    assert "<script" not in sanitized.lower()
