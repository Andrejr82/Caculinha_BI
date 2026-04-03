"""
Prepara o modelo local de embeddings no host.

Uso:
    python backend/scripts/maintenance/preload_embedding_model.py
    python backend/scripts/maintenance/preload_embedding_model.py --allow-download
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config.settings import settings
from backend.app.core.retrieval.embedding_backend import get_embedding_backend


def main() -> int:
    parser = argparse.ArgumentParser(description="Precarrega o modelo local de embeddings do ChatBI.")
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Permite download do modelo se ele ainda não estiver no cache local.",
    )
    args = parser.parse_args()

    backend = get_embedding_backend(settings.RAG_EMBEDDING_MODEL)
    ready = backend.warm_up(allow_download=args.allow_download)

    cache_dir = Path(settings.RAG_EMBEDDING_CACHE_DIR)
    print(
        {
            "model": settings.RAG_EMBEDDING_MODEL,
            "cache_dir": str(cache_dir),
            "local_files_only": settings.RAG_EMBEDDING_LOCAL_FILES_ONLY and not args.allow_download,
            "ready": ready,
        }
    )
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
