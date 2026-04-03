"""
Camada canônica de embeddings para retrieval local.

Separa embeddings do provider generativo e padroniza o uso de
sentence-transformers no runtime principal. Quando a dependência não está
disponível, usa fallback determinístico para não quebrar testes e fluxos
offline.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List, Optional

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:  # pragma: no cover - depende do ambiente
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning(
        "sentence-transformers não instalado. Usando fallback determinístico para embeddings."
    )


class EmbeddingBackend:
    """Backend local de embeddings com lazy loading e fallback determinístico."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        *,
        fallback_dimension: int = 384,
    ) -> None:
        self.model_name = model_name or settings.RAG_EMBEDDING_MODEL
        self.fallback_dimension = fallback_dimension
        self.cache_dir = Path(settings.RAG_EMBEDDING_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.local_files_only = settings.RAG_EMBEDDING_LOCAL_FILES_ONLY
        self._model = None
        self._disabled = False
        self._lock = threading.Lock()

    def _resolve_cached_model_path(self) -> Optional[Path]:
        model_path = Path(self.model_name)
        if model_path.exists():
            return model_path

        repo_cache_dir = self.cache_dir / f"models--{self.model_name.replace('/', '--')}"
        snapshots_dir = repo_cache_dir / "snapshots"
        if not snapshots_dir.exists():
            return None

        ref_path = repo_cache_dir / "refs" / "main"
        if ref_path.exists():
            snapshot_ref = ref_path.read_text(encoding="utf-8").strip()
            candidate = snapshots_dir / snapshot_ref
            if candidate.exists():
                return candidate

        snapshots = [path for path in snapshots_dir.iterdir() if path.is_dir()]
        if not snapshots:
            return None
        return max(snapshots, key=lambda path: path.stat().st_mtime)

    @contextmanager
    def _hf_offline_environment(self):
        overrides = {
            "HF_HOME": str(self.cache_dir),
            "HF_HUB_CACHE": str(self.cache_dir),
            "HUGGINGFACE_HUB_CACHE": str(self.cache_dir),
            "SENTENCE_TRANSFORMERS_HOME": str(self.cache_dir),
            "TRANSFORMERS_CACHE": str(self.cache_dir),
            "HF_HUB_DISABLE_TELEMETRY": "1",
        }
        if self.local_files_only:
            overrides["HF_HUB_OFFLINE"] = "1"
            overrides["TRANSFORMERS_OFFLINE"] = "1"

        previous = {key: os.environ.get(key) for key in overrides}
        try:
            for key, value in overrides.items():
                os.environ[key] = value
            yield
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _load_model(self):
        if self._model is not None:
            return self._model
        if self._disabled or not HAS_SENTENCE_TRANSFORMERS:
            return None

        with self._lock:
            if self._model is None and not self._disabled:
                logger.info("Carregando modelo de embeddings local: %s", self.model_name)
                try:
                    source = self.model_name
                    if self.local_files_only:
                        cached_model_path = self._resolve_cached_model_path()
                        if cached_model_path is None:
                            raise FileNotFoundError(
                                f"Modelo local não encontrado no cache: {self.model_name}"
                            )
                        source = str(cached_model_path)
                    with self._hf_offline_environment():
                        self._model = SentenceTransformer(
                            source,
                            cache_folder=str(self.cache_dir),
                            local_files_only=self.local_files_only,
                        )
                except Exception as exc:  # pragma: no cover - depende do ambiente/cache local
                    logger.warning(
                        "Falha ao carregar modelo local de embeddings (%s). Usando fallback determinístico.",
                        exc,
                    )
                    self._disabled = True
                    self._model = None
        return self._model

    @property
    def dimension(self) -> int:
        model = self._load_model()
        if model is not None and hasattr(model, "get_sentence_embedding_dimension"):
            dim = model.get_sentence_embedding_dimension()
            if isinstance(dim, int) and dim > 0:
                return dim
        return self.fallback_dimension

    def embed_text(self, text: str) -> List[float]:
        normalized = (text or "").strip()
        if not normalized:
            return []

        model = self._load_model()
        if model is None:
            return self._hash_embedding(normalized)

        vector = model.encode(normalized, normalize_embeddings=True)
        if hasattr(vector, "tolist"):
            return vector.tolist()
        return list(vector)

    def embed_batch(self, texts: Iterable[str]) -> List[List[float]]:
        items = [str(text or "").strip() for text in texts]
        if not items:
            return []

        model = self._load_model()
        if model is None:
            return [self._hash_embedding(item) if item else [] for item in items]

        vectors = model.encode(items, normalize_embeddings=True, show_progress_bar=False)
        return [vector.tolist() if hasattr(vector, "tolist") else list(vector) for vector in vectors]

    def cosine_similarity(self, left: List[float], right: List[float]) -> float:
        if not left or not right:
            return 0.0
        dot_product = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot_product / (left_norm * right_norm)

    def _hash_embedding(self, text: str) -> List[float]:
        values: List[float] = []
        seed = 0
        while len(values) < self.fallback_dimension:
            digest = hashlib.sha256(f"{seed}:{text}".encode("utf-8")).digest()
            seed += 1
            for idx in range(0, len(digest), 4):
                chunk = digest[idx : idx + 4]
                if len(chunk) < 4:
                    continue
                raw = int.from_bytes(chunk, byteorder="big", signed=False)
                values.append((raw / 2**32) * 2 - 1)
                if len(values) >= self.fallback_dimension:
                    break

        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            return values
        return [value / norm for value in values]

    def warm_up(self, *, allow_download: bool = False) -> bool:
        previous_local_only = self.local_files_only
        if allow_download:
            self.local_files_only = False
            self._disabled = False
        try:
            model = self._load_model()
            return model is not None
        finally:
            self.local_files_only = previous_local_only


_default_backend: Optional[EmbeddingBackend] = None


def get_embedding_backend(model_name: Optional[str] = None) -> EmbeddingBackend:
    global _default_backend
    if _default_backend is None or (model_name and _default_backend.model_name != model_name):
        _default_backend = EmbeddingBackend(model_name=model_name)
    return _default_backend
