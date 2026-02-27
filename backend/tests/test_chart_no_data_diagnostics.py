from types import SimpleNamespace

from backend.app.core.context import set_current_user_context
from backend.app.core.tools.universal_chart_generator import _build_no_data_payload


def test_no_data_payload_marks_rls_block_when_segment_is_not_allowed():
    set_current_user_context(SimpleNamespace(role="user", segments_list=["PAPELARIA"]))
    payload = _build_no_data_payload(
        descricao="grafico de vendas por loja",
        filtro_segmento="ARTES",
        lista_unes=[],
        filtro_categoria=None,
        lista_produtos=[],
    )

    assert payload["status"] == "error"
    assert payload["error_code"] == "NO_DATA"
    assert payload["diagnostics"]["rls_active"] is True
    assert payload["diagnostics"]["likely_rls_block"] is True


def test_no_data_payload_without_rls_restriction():
    set_current_user_context(SimpleNamespace(role="admin", segments_list=["*"]))
    payload = _build_no_data_payload(
        descricao="grafico de vendas por loja",
        filtro_segmento="ARTES",
        lista_unes=[],
        filtro_categoria=None,
        lista_produtos=[],
    )

    assert payload["status"] == "error"
    assert payload["error_code"] == "NO_DATA"
    assert payload["diagnostics"]["rls_active"] is False
    assert payload["diagnostics"]["likely_rls_block"] is False

