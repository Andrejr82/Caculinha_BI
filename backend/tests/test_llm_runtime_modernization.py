from pathlib import Path
from unittest.mock import patch

from backend.app.core.retrieval.embedding_backend import EmbeddingBackend
from backend.app.core.response_scorer import ResponseScorer
from backend.app.core.tools.tool_metadata import compose_tool_description
from backend.app.services.query_interpreter import QueryInterpreter, IntentType


class _FakeLLM:
    def __init__(self, content: str):
        self.content = content
        self.last_messages = None
        self.last_kwargs = None

    def generate_with_history(self, messages, **kwargs):
        self.last_messages = messages
        self.last_kwargs = kwargs
        return self.content


def test_query_interpreter_llm_prompt_uses_json_without_chain_of_thought():
    fake_llm = _FakeLLM('{"intent_type":"chat","entities":{},"confidence":0.91,"visualization":null}')
    interpreter = QueryInterpreter(llm_adapter=fake_llm)

    intent = interpreter._llm_classify("Como está o sistema?")

    prompt = fake_llm.last_messages[0]["content"]
    assert "CHAIN-OF-THOUGHT" not in prompt
    assert "pense em voz alta" not in prompt
    assert fake_llm.last_kwargs["json_mode"] is True
    assert intent.intent_type == IntentType.CHAT


def test_response_scorer_rewards_filter_preservation():
    scorer = ResponseScorer()

    result = scorer.score(
        prompt="Compare vendas da loja 1685 em papelaria nos últimos 30d",
        response="Loja 1685 em papelaria teve queda de 8% nos últimos 30d versus a base anterior.",
        latency_ms=800,
        retrieved_docs=["doc-1"],
    )

    assert result["dimension_scores"]["groundedness"] >= 80
    assert result["dimension_scores"]["correctness"] >= 70


def test_tool_metadata_enriches_description():
    description = compose_tool_description("buscar_produtos_inteligente", "fallback")

    assert "USE QUANDO" in description
    assert "NAO USE QUANDO" in description
    assert "descricao" in description


def test_embedding_backend_falls_back_when_model_is_unavailable():
    backend = EmbeddingBackend(model_name="missing-local-model", fallback_dimension=16)
    backend.local_files_only = True

    with patch("backend.app.core.retrieval.embedding_backend.SentenceTransformer", side_effect=RuntimeError("missing")):
        vector = backend.embed_text("cola bastao escolar")

    assert len(vector) == 16
    assert backend._disabled is True


def test_embedding_backend_uses_local_snapshot_path_when_offline(tmp_path: Path):
    snapshot_dir = (
        tmp_path
        / "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
        / "snapshots"
        / "snapshot-123"
    )
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "modules.json").write_text("{}", encoding="utf-8")

    backend = EmbeddingBackend(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        fallback_dimension=16,
    )
    backend.cache_dir = tmp_path
    backend.local_files_only = True

    with patch("backend.app.core.retrieval.embedding_backend.SentenceTransformer") as sentence_transformer:
        sentence_transformer.return_value = object()
        backend._load_model()

    source = sentence_transformer.call_args.args[0]
    assert Path(source) == snapshot_dir
