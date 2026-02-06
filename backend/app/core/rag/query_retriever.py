# backend/app/core/rag/query_retriever.py

from typing import Any, Dict, List, Optional
import os
import json
import functools # Added import

# Import ExampleCollector
from app.core.rag.example_collector import ExampleCollector
from app.config.settings import settings

# Placeholder for SentenceTransformer and FAISS.
# In a real implementation, these would be loaded conditionally/lazily.
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_RAG_DEPS = True
except (ImportError, OSError, Exception) as e: # Catch OSError for PyTorch/DLL issues
    print(f"Warning: RAG dependencies (sentence_transformers, faiss) failed to load: {e}. RAG functionality will be limited.")
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
            print("RAG dependencies not available. QueryRetriever will operate without semantic search.")

    @functools.lru_cache(maxsize=1) # Cache the model instance
    def _get_cached_model(self):
        """Internal method to get a cached SentenceTransformer model instance."""
        if not HAS_RAG_DEPS:
            return None
        try:
            model = SentenceTransformer(self.embedding_model_name)
            print(f"RAG: Loaded embedding model: {self.embedding_model_name}")
            return model
        except Exception as e:
            print(f"Error loading SentenceTransformer model: {e}")
            return None

    def _load_model(self):
        """Loads the Sentence Transformer model lazily using a cached internal method."""
        if self.model is None:
            self.model = self._get_cached_model()
    
    def _load_index_and_examples(self):
        """Loads FAISS index and corresponding examples data."""
        if not HAS_RAG_DEPS or self.model is None:
            print("RAG: Cannot load index or examples without model and dependencies.")
            return

        # Attempt to load examples data from ExampleCollector
        self.examples_data = self.example_collector.get_all_examples()
        if not self.examples_data:
            print("RAG: No examples found in collector to load or index.")
            return

        if not os.path.exists(self.faiss_index_path):
            print(f"RAG: FAISS index not found at {self.faiss_index_path}. Indexing examples...")
            self._index_examples_data()
            return

        try:
            self.index = faiss.read_index(self.faiss_index_path)
            print(f"RAG: Loaded FAISS index from {self.faiss_index_path}")
            print(f"RAG: Loaded {len(self.examples_data)} examples for RAG.")
        except Exception as e:
            print(f"Error loading FAISS index: {e}. Re-indexing...")
            self._index_examples_data()

    def _index_examples_data(self):
        """
        Indexes examples data (from self.examples_data) into FAISS.
        """
        if not HAS_RAG_DEPS or self.model is None:
            print("Cannot index examples: RAG dependencies or model not available.")
            return
        if not self.examples_data:
            print("No examples data to index.")
            return

        queries = [ex["query"] for ex in self.examples_data]
        embeddings = self.model.encode(queries, convert_to_numpy=True)

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        faiss.write_index(self.index, self.faiss_index_path)
        print(f"RAG: Indexed {len(self.examples_data)} examples and saved FAISS index.")

    def _index_examples_from_files(self):
        """
        (Deprecated) Collects and indexes examples from JSONL files in the examples_path.
        Now uses ExampleCollector.get_all_examples()
        """
        print("RAG: _index_examples_from_files is deprecated. Using ExampleCollector.")
        self.examples_data = self.example_collector.get_all_examples()
        self._index_examples_data()

    def get_similar_queries(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top_k semantically similar queries from the indexed examples.
        """
        if not HAS_RAG_DEPS or self.model is None or self.index is None:
            print("QueryRetriever: RAG not fully initialized. Returning empty list.")
            return []

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)

        similar_examples = []
        for i in indices[0]:
            if 0 <= i < len(self.examples_data): # Ensure index is valid
                similar_examples.append(self.examples_data[i])
        
        print(f"QueryRetriever: Found {len(similar_examples)} similar examples for query: '{query}'")
        return similar_examples

if __name__ == '__main__':
    # Setup dummy environment for testing
    from app.config.settings import Settings
    temp_settings = Settings()
    
    # Ensure data/learning directory exists
    os.makedirs(temp_settings.LEARNING_EXAMPLES_PATH, exist_ok=True)
    
    # Create some dummy example data
    dummy_examples = [
        {"query": "Mostre as vendas por produto no segmento A", "code": "code1", "result": "res1"},
        {"query": "Quantos produtos vendemos no segmento B", "code": "code2", "result": "res2"},
        {"query": "Analise o desempenho de vendas por categoria", "code": "code3", "result": "res3"},
        {"query": "Qual o total de vendas por segmento", "code": "code4", "result": "res4"},
    ]
    with open(os.path.join(temp_settings.LEARNING_EXAMPLES_PATH, "dummy_examples.jsonl"), 'w', encoding='utf-8') as f:
        for ex in dummy_examples:
            f.write(json.dumps(ex) + '\n')

    print("--- Testing QueryRetriever ---")
    retriever = QueryRetriever(
        embedding_model_name=temp_settings.RAG_EMBEDDING_MODEL,
        faiss_index_path=temp_settings.RAG_FAISS_INDEX_PATH,
        examples_path=temp_settings.LEARNING_EXAMPLES_PATH
    )

    if HAS_RAG_DEPS:
        # Test semantic search
        similar_queries = retriever.get_similar_queries("Quais foram os produtos mais vendidos por segmento?", top_k=2)
        print("\nSimilar queries found:")
        for q in similar_queries:
            print(f"- {q['query']}")
    else:
        print("\nSkipping semantic search test as RAG dependencies are not available.")

    # Clean up dummy files
    if os.path.exists(os.path.join(temp_settings.LEARNING_EXAMPLES_PATH, "dummy_examples.jsonl")):
        os.remove(os.path.join(temp_settings.LEARNING_EXAMPLES_PATH, "dummy_examples.jsonl"))
    if os.path.exists(temp_settings.RAG_FAISS_INDEX_PATH):
        os.remove(temp_settings.RAG_FAISS_INDEX_PATH)
    if os.path.exists(os.path.join(temp_settings.LEARNING_EXAMPLES_PATH, "indexed_examples.jsonl")):
        os.remove(os.path.join(temp_settings.LEARNING_EXAMPLES_PATH, "indexed_examples.jsonl"))
    print("\nCleaned up dummy RAG files.")
