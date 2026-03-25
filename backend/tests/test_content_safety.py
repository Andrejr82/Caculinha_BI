import pytest

from backend.app.core.security.content_safety import (
    sanitize_citations,
    validate_automation_action,
    validate_upload_filename,
)


def test_sanitize_citations_strips_active_content_and_bad_urls():
    citations = sanitize_citations(
        [
            {
                "source": "<b>Relatório</b><script>alert(1)</script>",
                "domain": "example.com",
                "url": "javascript:alert(1)",
                "competitor": "<img src=x onerror=alert(1)>",
            },
            {
                "source": "Fonte pública",
                "url": "https://example.com/evidencia",
            },
        ]
    )

    assert citations[0]["source"] == "Relatórioalert(1)"
    assert "url" not in citations[0]
    assert "competitor" not in citations[0]
    assert citations[1]["url"] == "https://example.com/evidencia"


def test_validate_upload_filename_rejects_path_traversal():
    with pytest.raises(ValueError):
        validate_upload_filename("../segredo.txt")


def test_validate_automation_action_blocks_shell_like_payload():
    with pytest.raises(ValueError):
        validate_automation_action(
            {
                "action": "browser.navigate",
                "params": {"target": "https://example.com && powershell -Command Remove-Item *"},
            }
        )
