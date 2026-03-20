import json

from backend.app.core.learning.chat_example_backfill import backfill_examples_from_session_db
from backend.app.core.utils.session_manager import SessionManager


def test_backfill_examples_from_session_db_imports_only_high_quality_examples(tmp_path):
    db_path = tmp_path / "agentbi.db"
    session_manager = SessionManager(
        storage_dir=str(tmp_path / "sessions"),
        db_path=str(db_path),
    )

    good_session = "11111111-1111-1111-1111-111111111111"
    bad_session = "22222222-2222-2222-2222-222222222222"
    user_id = "user-1"

    session_manager.add_message(
        good_session,
        "user",
        "quero um gráfico de vendas do segmento tecidos por loja",
        user_id,
        metadata={"request_id": "req-good"},
    )
    session_manager.add_message(
        good_session,
        "assistant",
        "Análise concluída com visualização gerada.",
        user_id,
        metadata={
            "request_id": "req-good",
            "source": "tool.consultar_dados_flexivel",
            "confidence": 0.92,
            "context": {"response_type": "chart", "has_chart": True, "segment": "TECIDOS"},
        },
    )

    session_manager.add_message(
        bad_session,
        "user",
        "me de o gráfico do segmento festas de cada loja",
        user_id,
        metadata={"request_id": "req-bad"},
    )
    session_manager.add_message(
        bad_session,
        "assistant",
        "Não consegui gerar o gráfico: Não encontrei dados para montar o gráfico nesse recorte.",
        user_id,
        metadata={
            "request_id": "req-bad",
            "source": "tool.gerar_grafico_universal_v2",
            "context": {"response_type": "chart", "has_chart": False, "segment": "FESTAS"},
        },
    )

    result = backfill_examples_from_session_db(
        db_path=str(db_path),
        examples_dir=str(tmp_path / "learning"),
        rebuild_dataset=False,
    )

    assert result == {"scanned": 2, "captured": 1, "skipped": 1, "duplicates": 0}

    example_files = sorted((tmp_path / "learning").glob("examples_*.jsonl"))
    assert len(example_files) == 1
    rows = [json.loads(line) for line in example_files[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["query"] == "quero um gráfico de vendas do segmento tecidos por loja"
    assert rows[0]["example_id"] == "req-good"
    assert rows[0]["assistant_response"] == "Análise concluída com visualização gerada."
