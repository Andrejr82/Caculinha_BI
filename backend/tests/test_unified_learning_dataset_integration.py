import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.app.core.learning.continuous_learner import ContinuousLearner
from backend.app.core.learning import unified_dataset_builder as unified_builder
from backend.app.core.learning.unified_dataset_builder import (
    UnifiedLearningDatasetBuilder,
    get_unified_dataset_status,
    get_unified_dataset_output_dir,
    get_unified_few_shot_path,
    get_unified_rag_corpus_path,
)
from backend.app.core.prompts import master_prompt
from backend.app.core.rag.example_collector import ExampleCollector


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_unified_dataset_builder_creates_runtime_artifacts(tmp_path):
    examples_dir = tmp_path / "learning"
    feedback_dir = tmp_path / "feedback"
    few_shot_path = tmp_path / "few_shot_examples.json"
    golden_path = tmp_path / "chatbi_golden_v1.json"
    intents_catalog_path = tmp_path / "bi_intents_catalog.json"
    templates_catalog_path = tmp_path / "bi_templates_catalog.json"

    _write_json(
        few_shot_path,
        {
            "examples": [
                {
                    "category": "grafico",
                    "user": "mostre vendas por segmento",
                    "assistant_reasoning": "usar grafico por segmento",
                    "assistant_response": "grafico gerado",
                    "tool_calls": [{"tool": "gerar_grafico_universal_v2"}],
                }
            ]
        },
    )
    _write_json(
        golden_path,
        {
            "cases": [
                {
                    "id": "golden-1",
                    "query": "avaliar margem por categoria",
                    "raw_response": "margem consolidada",
                    "expected_process": "comercial",
                }
            ]
        },
    )
    _write_json(
        intents_catalog_path,
        {
            "intents": [
                {
                    "id": "sql.ruptura_por_loja_periodo",
                    "description": "Retorna SQL para ruptura por loja e periodo",
                    "patterns": ["ruptura", "loja", "periodo"],
                    "default_confidence": 0.93,
                }
            ]
        },
    )
    _write_json(
        templates_catalog_path,
        {
            "templates": [
                {
                    "id": "bi.margem_categoria",
                    "keywords": ["margem", "categoria"],
                    "summary": "Template para análise de margem por categoria.",
                    "headers": ["Categoria", "Margem_%"],
                    "action": "Revisar preço e custo nas categorias abaixo da meta.",
                }
            ]
        },
    )
    _write_jsonl(
        feedback_dir / "feedback.jsonl",
        [
            {
                "query_text": "quais lojas venderam mais",
                "response_text": "loja 1685 lidera",
                "feedback_type": "positive",
                "confidence": 0.92,
            }
        ],
    )
    _write_jsonl(
        examples_dir / "examples_2026-03-08.jsonl",
        [
            {
                "timestamp": "2026-03-08T12:00:00",
                "user_id": "u1",
                "query": "sql de ruptura por loja",
                "code": "select * from ruptura",
                "result_summary": "consulta pronta",
                "intent": "sql",
            }
        ],
    )
    _write_json(
        examples_dir / "golden_dataset" / "positive" / "golden_positive.json",
        {
            "timestamp": "2026-03-08T13:00:00",
            "query": "previsao semanal por loja",
            "response": {"result": {"mensagem": "previsao montada"}},
            "confidence_score": 0.88,
            "tags": ["demanda"],
        },
    )

    builder = UnifiedLearningDatasetBuilder(
        examples_path=str(examples_dir),
        feedback_path=str(feedback_dir),
        few_shot_path=str(few_shot_path),
        golden_regression_path=str(golden_path),
        intents_catalog_path=str(intents_catalog_path),
        templates_catalog_path=str(templates_catalog_path),
    )
    manifest = builder.build()

    output_dir = get_unified_dataset_output_dir(str(examples_dir))
    assert manifest["records_total"] >= 5
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "unified_dataset.jsonl").exists()
    assert get_unified_few_shot_path(str(examples_dir)).exists()
    assert get_unified_rag_corpus_path(str(examples_dir)).exists()

    generated_few_shot = json.loads(get_unified_few_shot_path(str(examples_dir)).read_text(encoding="utf-8"))
    generated_users = {item["user"] for item in generated_few_shot["examples"]}
    assert "mostre vendas por segmento" in generated_users
    assert "avaliar margem por categoria" in generated_users
    assert manifest["source_counts"]["intents_catalog"] == 1
    assert manifest["source_counts"]["templates_catalog"] == 1
    assert manifest["completeness"]["runtime_ready"] is True
    assert manifest["completeness"]["production_ready"] is True


def test_master_prompt_prefers_generated_unified_few_shot(monkeypatch, tmp_path):
    few_shot_path = get_unified_few_shot_path(str(tmp_path))
    _write_json(
        few_shot_path,
        {
            "examples": [
                {
                    "category": "unified",
                    "user": "exemplo unificado",
                    "assistant_reasoning": "usar base unificada",
                    "assistant_response": "resposta unificada",
                }
            ]
        },
    )

    monkeypatch.setattr(unified_builder.settings, "LEARNING_EXAMPLES_PATH", str(tmp_path))

    examples = master_prompt.get_few_shot_examples()
    assert examples[0]["user"] == "exemplo unificado"


def test_master_prompt_formats_examples_without_reasoning(monkeypatch, tmp_path):
    few_shot_path = get_unified_few_shot_path(str(tmp_path))
    _write_json(
        few_shot_path,
        {
            "examples": [
                {
                    "category": "promotion",
                    "user": "vale fazer promocao?",
                    "assistant_reasoning": "nao deve aparecer no prompt",
                    "assistant_response": "resposta operacional",
                    "tool_calls": [{"tool": "simular_promocao_cesta", "parameters": {"desconto_pct": 10}}],
                }
            ]
        },
    )

    monkeypatch.setattr(unified_builder.settings, "LEARNING_EXAMPLES_PATH", str(tmp_path))

    prompt = master_prompt.get_system_prompt()

    assert "nao deve aparecer no prompt" not in prompt
    assert "Ferramentas esperadas" in prompt
    assert "simular_promocao_cesta" in prompt


def test_unified_dataset_status_reports_missing_real_world_sources(tmp_path):
    output_dir = get_unified_dataset_output_dir(str(tmp_path))
    manifest = {
        "dataset_version": "v2.0.0",
        "records_total": 10,
        "artifacts": {
            "dataset": str(output_dir / "unified_dataset.jsonl"),
            "few_shot": str(output_dir / "few_shot_examples.json"),
            "rag_corpus": str(output_dir / "rag_corpus.jsonl"),
        },
        "completeness": {
            "runtime_ready": True,
            "production_ready": False,
            "missing_runtime_sources": [],
            "missing_production_sources": ["feedback", "example_collector", "continuous_positive"],
            "missing_recommended_sources": ["continuous_review"],
            "artifact_presence": {"dataset": True, "few_shot": True, "rag_corpus": True},
            "records_total_sufficient": False,
            "recommendations": ["Coletar perguntas reais"],
        },
    }
    for file_name in ("unified_dataset.jsonl", "few_shot_examples.json", "rag_corpus.jsonl"):
        (output_dir / file_name).parent.mkdir(parents=True, exist_ok=True)
        (output_dir / file_name).write_text("{}", encoding="utf-8")
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    status = get_unified_dataset_status(str(tmp_path))

    assert status["exists"] is True
    assert status["completeness"]["production_ready"] is False
    assert "feedback" in status["completeness"]["missing_production_sources"]


def test_example_collector_merges_generated_unified_rag_corpus(tmp_path):
    collector = ExampleCollector(examples_dir=str(tmp_path))
    collector.add_example(
        user_id="u1",
        query="consulta diaria",
        code="select 1",
        result={"result": "ok"},
        intent="sql",
        timestamp=datetime(2026, 3, 8, 12, 0, 0),
    )
    _write_jsonl(
        get_unified_rag_corpus_path(str(tmp_path)),
        [{"query": "consulta curada", "response": "resposta curada", "source_type": "golden"}],
    )

    examples = collector.get_all_examples()
    queries = {item["query"] for item in examples}

    assert "consulta diaria" in queries
    assert "consulta curada" in queries


@pytest.mark.asyncio
async def test_continuous_learner_rebuilds_unified_dataset_on_feedback(tmp_path):
    learner = ContinuousLearner(
        golden_dataset_path=str(tmp_path / "golden_dataset"),
        feedback_buffer_size=50,
        auto_optimize=False,
    )

    with patch(
        "backend.app.core.learning.unified_dataset_builder.build_default_unified_learning_dataset"
    ) as mock_rebuild:
        result = await learner.process_interaction(
            query="quais lojas venderam mais",
            response={"response_text": "loja 1685 lidera"},
            feedback_type="positive",
            confidence_score=0.91,
            session_id="sessao-1",
            user_id="u1",
        )

    assert "added_to_golden_dataset" in result["actions_taken"]
    mock_rebuild.assert_called_once()
