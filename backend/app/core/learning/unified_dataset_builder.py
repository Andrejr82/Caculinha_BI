import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

UNIFIED_DATASET_VERSION = "v2.0.0"
UNIFIED_DATASET_DIRNAME = "unified_dataset_v2"
UNIFIED_DATASET_FILENAME = "unified_dataset.jsonl"
UNIFIED_FEW_SHOT_FILENAME = "few_shot_examples.json"
UNIFIED_RAG_FILENAME = "rag_corpus.jsonl"
UNIFIED_MANIFEST_FILENAME = "manifest.json"
REQUIRED_RUNTIME_SOURCES = ("few_shot", "golden_regression")
REQUIRED_PRODUCTION_SOURCES = ("feedback", "example_collector", "continuous_positive")
RECOMMENDED_SOURCES = ("continuous_review",)


def get_unified_dataset_output_dir(base_dir: Optional[str] = None) -> Path:
    root = Path(base_dir or settings.LEARNING_EXAMPLES_PATH)
    return root / UNIFIED_DATASET_DIRNAME


def get_unified_few_shot_path(base_dir: Optional[str] = None) -> Path:
    return get_unified_dataset_output_dir(base_dir) / UNIFIED_FEW_SHOT_FILENAME


def get_unified_rag_corpus_path(base_dir: Optional[str] = None) -> Path:
    return get_unified_dataset_output_dir(base_dir) / UNIFIED_RAG_FILENAME


def get_unified_manifest_path(base_dir: Optional[str] = None) -> Path:
    return get_unified_dataset_output_dir(base_dir) / UNIFIED_MANIFEST_FILENAME


def _compute_dataset_completeness(
    source_counts: Dict[str, int],
    artifacts: Dict[str, str],
    *,
    records_total: int,
) -> Dict[str, Any]:
    artifact_presence = {
        name: Path(path).exists()
        for name, path in artifacts.items()
    }
    runtime_ready = all(source_counts.get(source, 0) > 0 for source in REQUIRED_RUNTIME_SOURCES) and all(
        artifact_presence.values()
    )
    production_ready = runtime_ready and all(
        source_counts.get(source, 0) > 0 for source in REQUIRED_PRODUCTION_SOURCES
    )
    missing_runtime_sources = [source for source in REQUIRED_RUNTIME_SOURCES if source_counts.get(source, 0) <= 0]
    missing_production_sources = [source for source in REQUIRED_PRODUCTION_SOURCES if source_counts.get(source, 0) <= 0]
    missing_recommended_sources = [source for source in RECOMMENDED_SOURCES if source_counts.get(source, 0) <= 0]

    recommendations: List[str] = []
    if missing_production_sources:
        recommendations.append(
            "Coletar perguntas reais e feedback validado para preencher as fontes: "
            + ", ".join(missing_production_sources)
        )
    if missing_recommended_sources:
        recommendations.append(
            "Adicionar fila de review humano ao corpus unificado para cobrir casos negativos/duvidosos."
        )
    if records_total < 25:
        recommendations.append(
            "Aumentar o volume do dataset unificado; abaixo de 25 registros a cobertura ainda é baixa para produção."
        )

    return {
        "runtime_ready": runtime_ready,
        "production_ready": production_ready,
        "records_total_sufficient": records_total >= 25,
        "artifact_presence": artifact_presence,
        "missing_runtime_sources": missing_runtime_sources,
        "missing_production_sources": missing_production_sources,
        "missing_recommended_sources": missing_recommended_sources,
        "recommendations": recommendations,
    }


def get_unified_dataset_status(base_dir: Optional[str] = None, rebuild_if_missing: bool = False) -> Dict[str, Any]:
    manifest_path = get_unified_manifest_path(base_dir)
    if not manifest_path.exists():
        if not rebuild_if_missing:
            return {
                "exists": False,
                "manifest_path": str(manifest_path),
                "completeness": {
                    "runtime_ready": False,
                    "production_ready": False,
                    "records_total_sufficient": False,
                    "artifact_presence": {},
                    "missing_runtime_sources": list(REQUIRED_RUNTIME_SOURCES),
                    "missing_production_sources": list(REQUIRED_PRODUCTION_SOURCES),
                    "missing_recommended_sources": list(RECOMMENDED_SOURCES),
                    "recommendations": ["Gerar o dataset unificado antes de usar prompt/RAG com a base consolidada."],
                },
            }
        build_default_unified_learning_dataset()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "manifest_path": str(manifest_path),
        **payload,
    }


class UnifiedLearningDatasetBuilder:
    def __init__(
        self,
        *,
        examples_path: Optional[str] = None,
        feedback_path: Optional[str] = None,
        few_shot_path: Optional[str] = None,
        golden_regression_path: Optional[str] = None,
        intents_catalog_path: Optional[str] = None,
        templates_catalog_path: Optional[str] = None,
    ) -> None:
        self.examples_path = Path(examples_path or settings.LEARNING_EXAMPLES_PATH)
        self.feedback_path = Path(feedback_path or settings.LEARNING_FEEDBACK_PATH)
        backend_root = Path(__file__).resolve().parents[3]
        self.few_shot_path = Path(
            few_shot_path
            or backend_root / "prompts" / "few_shot_examples.json"
        )
        self.golden_regression_path = Path(
            golden_regression_path
            or backend_root
            / "tests"
            / "llmops"
            / "datasets"
            / "chatbi_golden_v1.json"
        )
        self.intents_catalog_path = Path(
            intents_catalog_path
            or backend_root
            / "app"
            / "core"
            / "prompts"
            / "bi_intents_catalog.json"
        )
        self.templates_catalog_path = Path(
            templates_catalog_path
            or backend_root
            / "app"
            / "core"
            / "prompts"
            / "bi_templates_catalog.json"
        )
        self.output_dir = get_unified_dataset_output_dir(str(self.examples_path))

    def build(self) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        records: List[Dict[str, Any]] = []
        records.extend(self._load_few_shot_records())
        records.extend(self._load_golden_regression_records())
        records.extend(self._load_intents_catalog_records())
        records.extend(self._load_templates_catalog_records())
        records.extend(self._load_feedback_records())
        records.extend(self._load_daily_example_records())
        records.extend(self._load_continuous_learning_records("positive"))
        records.extend(self._load_continuous_learning_records("review"))

        normalized_records = [record for record in records if self._is_valid_record(record)]
        prompt_examples = self._build_prompt_examples(normalized_records)
        rag_corpus = self._build_rag_corpus(normalized_records)

        self._write_jsonl(self.output_dir / UNIFIED_DATASET_FILENAME, normalized_records)
        self._write_json(self.output_dir / UNIFIED_FEW_SHOT_FILENAME, {"examples": prompt_examples})
        self._write_jsonl(self.output_dir / UNIFIED_RAG_FILENAME, rag_corpus)

        source_counts = Counter(str(record.get("source_type") or "unknown") for record in normalized_records)
        for required in (*REQUIRED_RUNTIME_SOURCES, *REQUIRED_PRODUCTION_SOURCES, *RECOMMENDED_SOURCES):
            source_counts.setdefault(required, 0)
        artifacts = {
            "dataset": str(self.output_dir / UNIFIED_DATASET_FILENAME),
            "few_shot": str(self.output_dir / UNIFIED_FEW_SHOT_FILENAME),
            "rag_corpus": str(self.output_dir / UNIFIED_RAG_FILENAME),
        }
        manifest = {
            "dataset_version": UNIFIED_DATASET_VERSION,
            "created_at": datetime.now().isoformat(),
            "output_dir": str(self.output_dir),
            "records_total": len(normalized_records),
            "few_shot_examples_total": len(prompt_examples),
            "rag_documents_total": len(rag_corpus),
            "source_counts": dict(source_counts),
            "completeness": _compute_dataset_completeness(
                dict(source_counts),
                artifacts,
                records_total=len(normalized_records),
            ),
            "source_files": {
                "few_shot": str(self.few_shot_path),
                "golden_regression": str(self.golden_regression_path),
                "intents_catalog": str(self.intents_catalog_path),
                "templates_catalog": str(self.templates_catalog_path),
                "feedback": str(self.feedback_path / "feedback.jsonl"),
                "examples_path": str(self.examples_path),
            },
            "artifacts": artifacts,
        }
        self._write_json(self.output_dir / UNIFIED_MANIFEST_FILENAME, manifest)
        return manifest

    def _load_few_shot_records(self) -> List[Dict[str, Any]]:
        if not self.few_shot_path.exists():
            return []
        payload = json.loads(self.few_shot_path.read_text(encoding="utf-8"))
        records = []
        for index, item in enumerate(payload.get("examples", [])):
            records.append(
                self._make_record(
                    record_id=f"few-shot-{index}",
                    source_type="few_shot",
                    query=item.get("user"),
                    assistant_response=item.get("assistant_response"),
                    assistant_reasoning=item.get("assistant_reasoning"),
                    tool_calls=item.get("tool_calls"),
                    intent=item.get("category"),
                    tags=[item.get("category")] if item.get("category") else [],
                    eligible_for_few_shot=True,
                    eligible_for_retrieval=True,
                    priority=100,
                )
            )
        return records

    def _load_golden_regression_records(self) -> List[Dict[str, Any]]:
        if not self.golden_regression_path.exists():
            return []
        payload = json.loads(self.golden_regression_path.read_text(encoding="utf-8"))
        records = []
        for item in payload.get("cases", []):
            process = str(item.get("expected_process") or "").strip()
            records.append(
                self._make_record(
                    record_id=f"golden-{item.get('id')}",
                    source_type="golden_regression",
                    query=item.get("query"),
                    assistant_response=item.get("raw_response"),
                    assistant_reasoning=f"Exemplo executivo curado para o processo {process}." if process else "",
                    intent=process or None,
                    tags=[process] if process else [],
                    eligible_for_few_shot=True,
                    eligible_for_retrieval=True,
                    priority=90,
                )
            )
        return records

    def _load_feedback_records(self) -> List[Dict[str, Any]]:
        feedback_file = self.feedback_path / "feedback.jsonl"
        if not feedback_file.exists():
            return []

        records = []
        for index, entry in enumerate(self._read_jsonl(feedback_file)):
            feedback_type = self._normalize_feedback_type(entry.get("feedback_type"))
            query_text = entry.get("query_text")
            response_text = entry.get("response_text")
            if not query_text or not response_text:
                continue
            records.append(
                self._make_record(
                    record_id=f"feedback-{index}",
                    source_type="feedback",
                    query=query_text,
                    assistant_response=response_text,
                    assistant_reasoning=entry.get("comment"),
                    intent=entry.get("mode"),
                    tags=[feedback_type] if feedback_type else [],
                    feedback_type=feedback_type,
                    confidence_score=entry.get("confidence"),
                    eligible_for_few_shot=feedback_type in {"positive", "partial"},
                    eligible_for_retrieval=feedback_type != "negative",
                    priority=80 if feedback_type == "positive" else 50,
                )
            )
        return records

    def _load_intents_catalog_records(self) -> List[Dict[str, Any]]:
        if not self.intents_catalog_path.exists():
            return []
        payload = json.loads(self.intents_catalog_path.read_text(encoding="utf-8"))
        records = []
        for item in payload.get("intents", []):
            patterns = [self._clean_text(pattern) for pattern in (item.get("patterns") or []) if self._clean_text(pattern)]
            description = self._clean_text(item.get("description"))
            records.append(
                self._make_record(
                    record_id=f"intent-{self._clean_text(item.get('id')) or len(records)}",
                    source_type="intents_catalog",
                    query=description or " ".join(patterns),
                    assistant_response=description or " ".join(patterns),
                    assistant_reasoning="Intent oficial do catalogo operacional do Playground BI.",
                    intent=item.get("id"),
                    tags=patterns,
                    confidence_score=item.get("default_confidence"),
                    eligible_for_few_shot=False,
                    eligible_for_retrieval=True,
                    priority=35,
                )
            )
        return records

    def _load_templates_catalog_records(self) -> List[Dict[str, Any]]:
        if not self.templates_catalog_path.exists():
            return []
        payload = json.loads(self.templates_catalog_path.read_text(encoding="utf-8"))
        records = []
        for item in payload.get("templates", []):
            keywords = [self._clean_text(keyword) for keyword in (item.get("keywords") or []) if self._clean_text(keyword)]
            query_text = self._clean_text(item.get("summary")) or " ".join(keywords)
            headers = [self._clean_text(header) for header in (item.get("headers") or []) if self._clean_text(header)]
            action = self._clean_text(item.get("action"))
            response_parts = [self._clean_text(item.get("summary"))]
            if headers:
                response_parts.append("Cabecalhos: " + ", ".join(headers))
            if action:
                response_parts.append("Acao sugerida: " + action)
            records.append(
                self._make_record(
                    record_id=f"template-{self._clean_text(item.get('id')) or len(records)}",
                    source_type="templates_catalog",
                    query=query_text,
                    assistant_response=" ".join(part for part in response_parts if part),
                    assistant_reasoning="Template oficial do catalogo Playground BI para respostas operacionais.",
                    intent=item.get("id"),
                    tags=keywords,
                    eligible_for_few_shot=False,
                    eligible_for_retrieval=True,
                    priority=30,
                )
            )
        return records

    def _load_daily_example_records(self) -> List[Dict[str, Any]]:
        if not self.examples_path.exists():
            return []

        records = []
        for file_path in sorted(self.examples_path.glob("examples_*.jsonl")):
            for index, entry in enumerate(self._read_jsonl(file_path)):
                metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
                assistant_response = entry.get("assistant_response") or entry.get("result_summary")
                records.append(
                    self._make_record(
                        record_id=str(entry.get("example_id") or f"example-{file_path.stem}-{index}"),
                        source_type="example_collector",
                        query=entry.get("query"),
                        assistant_response=assistant_response,
                        assistant_reasoning=entry.get("code"),
                        tool_calls=metadata.get("tool_calls"),
                        intent=entry.get("intent"),
                        tags=list(metadata.get("tags") or []),
                        confidence_score=metadata.get("confidence_score") or metadata.get("confidence"),
                        eligible_for_few_shot=False,
                        eligible_for_retrieval=True,
                        priority=55 if assistant_response else 40,
                    )
                )
        return records

    def _load_continuous_learning_records(self, bucket: str) -> List[Dict[str, Any]]:
        base_dir = self.examples_path / "golden_dataset" / bucket
        if not base_dir.exists():
            return []

        records = []
        for file_path in sorted(base_dir.glob("*.json")):
            try:
                entry = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("unified_dataset_invalid_json: %s", file_path)
                continue
            response_text = self._extract_response_text(entry.get("response"))
            records.append(
                self._make_record(
                    record_id=f"{bucket}-{file_path.stem}",
                    source_type=f"continuous_{bucket}",
                    query=entry.get("query"),
                    assistant_response=response_text,
                    assistant_reasoning="Exemplo gerado pelo continuous learner.",
                    intent=None,
                    tags=list(entry.get("tags") or []),
                    confidence_score=entry.get("confidence_score"),
                    eligible_for_few_shot=bucket == "positive",
                    eligible_for_retrieval=bucket == "positive",
                    priority=85 if bucket == "positive" else 20,
                )
            )
        return records

    def _make_record(
        self,
        *,
        record_id: str,
        source_type: str,
        query: Any,
        assistant_response: Any,
        assistant_reasoning: Any = "",
        tool_calls: Optional[Any] = None,
        intent: Optional[Any] = None,
        tags: Optional[Iterable[Any]] = None,
        feedback_type: Optional[Any] = None,
        confidence_score: Optional[Any] = None,
        eligible_for_few_shot: bool,
        eligible_for_retrieval: bool,
        priority: int,
    ) -> Dict[str, Any]:
        return {
            "id": record_id,
            "source_type": source_type,
            "query": self._clean_text(query),
            "assistant_response": self._clean_text(assistant_response),
            "assistant_reasoning": self._clean_text(assistant_reasoning),
            "tool_calls": tool_calls if isinstance(tool_calls, list) else [],
            "intent": self._clean_text(intent),
            "tags": [self._clean_text(tag) for tag in (tags or []) if self._clean_text(tag)],
            "feedback_type": self._normalize_feedback_type(feedback_type),
            "confidence_score": self._coerce_float(confidence_score),
            "eligible_for_few_shot": bool(eligible_for_few_shot),
            "eligible_for_retrieval": bool(eligible_for_retrieval),
            "priority": int(priority),
        }

    def _build_prompt_examples(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates = [
            record for record in records
            if record.get("eligible_for_few_shot") and record.get("query") and record.get("assistant_response")
        ]
        deduped = self._dedupe_records(candidates)
        selected = sorted(deduped, key=lambda item: (-int(item.get("priority", 0)), item.get("query", "")))[:12]
        return [
            {
                "category": record.get("intent") or record.get("source_type") or "general",
                "user": record.get("query"),
                "assistant_reasoning": record.get("assistant_reasoning") or f"Exemplo derivado de {record.get('source_type')}.",
                "tool_calls": record.get("tool_calls") or [],
                "assistant_response": record.get("assistant_response"),
                "source_type": record.get("source_type"),
            }
            for record in selected
        ]

    def _build_rag_corpus(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        candidates = [
            record for record in records
            if record.get("eligible_for_retrieval") and record.get("query") and record.get("assistant_response")
        ]
        deduped = self._dedupe_records(candidates)
        return [
            {
                "query": record.get("query"),
                "response": record.get("assistant_response"),
                "intent": record.get("intent"),
                "source_type": record.get("source_type"),
                "tags": record.get("tags") or [],
                "confidence_score": record.get("confidence_score"),
            }
            for record in sorted(deduped, key=lambda item: (-int(item.get("priority", 0)), item.get("query", "")))
        ]

    def _dedupe_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        best_by_query: Dict[str, Dict[str, Any]] = {}
        for record in records:
            query_key = self._clean_text(record.get("query")).lower()
            if not query_key:
                continue
            current = best_by_query.get(query_key)
            if current is None or int(record.get("priority", 0)) > int(current.get("priority", 0)):
                best_by_query[query_key] = record
        return list(best_by_query.values())

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_jsonl(self, path: Path, items: List[Dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    def _read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("unified_dataset_invalid_jsonl: %s", path)
        return items

    def _extract_response_text(self, payload: Any) -> str:
        if isinstance(payload, str):
            return self._clean_text(payload)
        if isinstance(payload, dict):
            if isinstance(payload.get("response_text"), str):
                return self._clean_text(payload.get("response_text"))
            if isinstance(payload.get("assistant_response"), str):
                return self._clean_text(payload.get("assistant_response"))
            result = payload.get("result")
            if isinstance(result, dict) and isinstance(result.get("mensagem"), str):
                return self._clean_text(result.get("mensagem"))
            if isinstance(result, str):
                return self._clean_text(result)
        return self._clean_text(payload)

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return " ".join(str(value).strip().split())

    def _coerce_float(self, value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _normalize_feedback_type(self, feedback_type: Any) -> str:
        normalized = self._clean_text(feedback_type).lower()
        if normalized in {"useful", "positive", "thumbs_up"}:
            return "positive"
        if normalized in {"not_useful", "negative", "thumbs_down"}:
            return "negative"
        if normalized == "partial":
            return "partial"
        return normalized

    def _is_valid_record(self, record: Dict[str, Any]) -> bool:
        return bool(record.get("query"))


def build_default_unified_learning_dataset() -> Dict[str, Any]:
    builder = UnifiedLearningDatasetBuilder()
    manifest = builder.build()
    logger.info("unified_learning_dataset_built: %s", manifest)
    return manifest
