# backend/app/core/rag/query_retriever.py

from typing import Any, Dict, List, Optional
import os
import json
import logging
import functools # Added import

# Import ExampleCollector
from backend.app.core.rag.example_collector import ExampleCollector
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

# Placeholder for SentenceTransformer and FAISS.
# In a real implementation, these would be loaded conditionally/lazily.
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_RAG_DEPS = True
except (ImportError, OSError, Exception) as e: # Catch OSError for PyTorch/DLL issues
    logger.warning(
        "RAG dependencies (sentence_transformers, faiss) failed to load: %s. RAG functionality will be limited.",
        e,
    )
    HAS_RAG_DEPS = False

class QueryRetriever:
    """
    Retrieves semantically similar past queries and their associated metadata (code, results)
    to serve as few-shot examples for RAG.
    (T6.4.1 from TASK_LIST)
    """
    def __init__(self, embedding_model_name: str = settings.RAG_EMBEDDING_MODEL, faiss_index_path: str = settings.RAG_FAISS_INDEX_PATH, examples_path: str = settings.LEARNING_EXAMPLES_PATH):
        self.embedding_model_name = embedding_model_name
        self.faiss_index_path = faiss_index_path
        self.examples_path = examples_path # Used by ExampleCollector
        self.model = None
        self.index = None
        self.examples_data: List[Dict[str, Any]] = [] # Stored as a list of dicts

        self.example_collector = ExampleCollector(examples_dir=self.examples_path)

        if HAS_RAG_DEPS:
            self._load_model()
            self._load_index_and_examples()
        else:
            logger.info("RAG dependencies not available. QueryRetriever will operate without semantic search.")

    @functools.lru_cache(maxsize=1) # Cache the model instance
    def _get_cached_model(self):
        """Internal method to get a cached SentenceTransformer model instance."""
        if not HAS_RAG_DEPS:
            return None
        try:
            model = SentenceTransformer(self.embedding_model_name)
            logger.info("RAG: Loaded embedding model %s", self.embedding_model_name)
            return model
        except Exception as e:
            logger.warning("Error loading SentenceTransformer model: %s", e)
            return None

    def _load_model(self):
        """Loads the Sentence Transformer model lazily using a cached internal method."""
        if self.model is None:
            self.model = self._get_cached_model()
    
    def _load_index_and_examples(self):
        """Loads FAISS index and corresponding examples data."""
        if not HAS_RAG_DEPS or self.model is None:
            logger.info("RAG: Cannot load index or examples without model and dependencies.")
            return

        # Attempt to load examples data from ExampleCollector
        self.examples_data = self.example_collector.get_all_examples()
        if not self.examples_data:
            logger.info("RAG: No examples found in collector to load or index.")
            return

        if not os.path.exists(self.faiss_index_path):
            logger.info("RAG: FAISS index not found at %s. Indexing examples...", self.faiss_index_path)
            self._index_examples_data()
            return

        try:
            self.index = faiss.read_index(self.faiss_index_path)
            logger.info("RAG: Loaded FAISS index from %s", self.faiss_index_path)
            logger.info("RAG: Loaded %s examples for RAG", len(self.examples_data))
        except Exception as e:
            logger.warning("Error loading FAISS index: %s. Re-indexing...", e)
            self._index_examples_data()

    def _index_examples_data(self):
        """
        Indexes examples data (from self.examples_data) into FAISS.
        """
        if not HAS_RAG_DEPS or self.model is None:
            logger.info("Cannot index examples: RAG dependencies or model not available.")
            return
        if not self.examples_data:
            logger.info("No examples data to index.")
            return

        queries = [ex["query"] for ex in self.examples_data]
        embeddings = self.model.encode(queries, convert_to_numpy=True)

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        faiss.write_index(self.index, self.faiss_index_path)
        logger.info("RAG: Indexed %s examples and saved FAISS index", len(self.examples_data))

    def _index_examples_from_files(self):
        """
        (Deprecated) Collects and indexes examples from JSONL files in the examples_path.
        Now uses ExampleCollector.get_all_examples()
        """
        logger.warning("RAG: _index_examples_from_files is deprecated. Using ExampleCollector.")
        self.examples_data = self.example_collector.get_all_examples()
        self._index_examples_data()

    def get_similar_queries(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top_k semantically similar queries from the indexed examples.
        """
        if not HAS_RAG_DEPS or self.model is None or self.index is None:
            logger.info("QueryRetriever: RAG not fully initialized. Returning empty list.")
            return []

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)

        similar_examples = []
        for i in indices[0]:
            if 0 <= i < len(self.examples_data): # Ensure index is valid
                similar_examples.append(self.examples_data[i])
        
        logger.info("QueryRetriever: Found %s similar examples", len(similar_examples))
        return similar_examples

