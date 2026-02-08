"""
Code RAG Service - Semantic Code Search with LlamaIndex + Gemini
================================================================

Provides semantic search and analysis of the entire codebase using:
- LlamaIndex for RAG (Retrieval-Augmented Generation)
- Gemini 3.0 Flash for LLM
- GeminiEmbedding for semantic search
- FAISS for vector storage

Author: Antigravity AI
Date: 2025-12-15
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.app.config.settings import settings

logger = logging.getLogger(__name__)


class CodeRAGService:
    """
    Service for semantic code search and analysis using RAG.
    
    Features:
    - Semantic search across entire codebase
    - Context-aware code analysis
    - Intelligent code suggestions
    - Multi-language support (Python, TypeScript, etc.)
    """
    
    def __init__(self):
        """Initialize the RAG service with lazy loading."""
        # Melhor prática Context7: Usar caminho absoluto baseado no arquivo, não no CWD
        # ./backend/app/core/code_rag_service.py -> ../../../storage
        self._storage_path = Path(__file__).resolve().parents[3] / "storage"
        self._initialized = False
        self._index_stats = None
        self._index = None
        self._query_engine = None
        
    def _ensure_initialized(self) -> bool:
        """
        Lazy initialization of the RAG engine.
        Only loads when first query is made.
        
        Returns:
            bool: True if initialized successfully
        """
        if self._initialized:
            return True
            
        try:
            logger.info("Initializing Code RAG Service...")
            logger.info(f"Storage Path: {self._storage_path}")
            
            # Check if Gemini API key is configured
            if not settings.GEMINI_API_KEY:
                logger.error("[ERROR] GEMINI_API_KEY not configured. Cannot initialize RAG service.")
                return False

            # Check if storage directory exists
            if not self._storage_path.exists():
                logger.error(f"[ERROR] Storage path does not exist: {self._storage_path}")
                logger.error("[ACTION REQUIRED] Run 'python scripts/index_codebase.py' to generate the index.")
                return False
                
            # Check for essential index files (simple validation)
            if not (self._storage_path / "docstore.json").exists() and not (self._storage_path / "index_store.json").exists():
                 logger.warning(f"[WARN] Index files not found in {self._storage_path}. Service might fail to load index.")

            # Import LlamaIndex components (lazy import)
            try:
                from llama_index.core import (
                    VectorStoreIndex,
                    Settings,
                    load_index_from_storage,
                )
                from llama_index.core.storage import StorageContext
                from llama_index.llms.gemini import Gemini
                from llama_index.embeddings.gemini import GeminiEmbedding
            except ImportError as e:
                logger.error(f"[ERROR] Missing dependencies (ImportError): {e}")
                logger.error("[ACTION REQUIRED] Install dependencies with 'pip install llama-index llama-index-llms-gemini llama-index-embeddings-gemini'")
                return False
            
            # Configure LlamaIndex Settings
            # Using gemini-3-flash-preview as requested
            try:
                Settings.llm = Gemini(
                    model_name="models/gemini-3-flash-preview", 
                    api_key=settings.GEMINI_API_KEY,
                    temperature=0.1,
                )
                
                Settings.embed_model = GeminiEmbedding(
                    model_name="models/text-embedding-004",
                    api_key=settings.GEMINI_API_KEY,
                )
            except Exception as e:
                logger.error(f"[ERROR] Failed to configure Gemini models: {e}")
                return False
            
            # Load index
            logger.info("Loading index from storage...")
            try:
                storage_context = StorageContext.from_defaults(
                    persist_dir=str(self._storage_path)
                )
                
                self._index = load_index_from_storage(storage_context)
                self._query_engine = self._index.as_query_engine(
                    similarity_top_k=5,
                    response_mode="tree_summarize"
                )
            except Exception as e:
                logger.error(f"[ERROR] Failed to load index from storage: {e}")
                logger.error("[ACTION REQUIRED] The index might be corrupted or incompatible. Try re-running 'python scripts/index_codebase.py'.")
                return False
            
            # Load index statistics
            stats_file = self._storage_path / "index_stats.json"
            if stats_file.exists():
                try:
                    with open(stats_file, 'r', encoding='utf-8') as f:
                        self._index_stats = json.load(f)
                except Exception as e:
                    logger.warning(f"[WARN] Failed to load index stats: {e}")
            
            self._initialized = True
            logger.info("Code RAG Service initialized successfully")
            return True
            
        except Exception as e:
            # CRITICAL: Log the full traceback to understand why it fails
            import traceback
            trace = traceback.format_exc()
            logger.error(f"[FATAL] Failed to initialize RAG service: {e}\n{trace}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the code index.

        Returns:
            Dict with index statistics
        """
        # Ensure service is initialized before returning stats
        self._ensure_initialized()

        if self._index_stats:
            return self._index_stats

        # Default stats if not loaded
        return {
            "status": "not_indexed",
            "total_files": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_lines": 0,
            "indexed_at": None,
            "languages": []
        }
    
    def stream_query(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        filters: Optional[Dict[str, Any]] = None
    ):
        """
        Query the codebase with streaming response.
        
        Args:
            message: User's question
            history: Conversation history
            filters: Optional filters
            
        Yields:
            Dicts with 'type' ('token', 'references', 'error') and payload
        """
        if not self._ensure_initialized():
            yield {
                "type": "error",
                "content": "Service not initialized. Check logs."
            }
            return

        try:
            # Build context
            context_messages = []
            if history:
                for msg in history[-5:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    context_messages.append(f"{role}: {content}")
            
            full_query = message
            if context_messages:
                context_str = "\n".join(context_messages)
                full_query = f"Contexto da conversa:\n{context_str}\n\nPergunta atual: {message}"

            # Create a streaming query engine specifically for this request
            # This is lightweight enough and ensures we don't mess up the cached sync engine
            streaming_engine = self._index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize",
                streaming=True
            )
            
            logger.info(f"[STREAM] Querying codebase: {message[:50]}...")
            
            # Execute query - returns a StreamingResponse
            response = streaming_engine.query(full_query)
            
            # 1. Yield Source Nodes (References) immediately
            code_references = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes[:5]:
                    metadata = node.node.metadata
                    code_references.append({
                        "file": metadata.get("file_path", "unknown"),
                        "score": node.score,
                        "content": node.node.text[:500],
                        "lines": str(metadata.get("lines", "")),
                    })
            
            yield {
                "type": "references",
                "references": code_references
            }
            
            # 2. Yield Tokens
            for text in response.response_gen:
                yield {
                    "type": "token",
                    "text": text
                }
                
        except Exception as e:
            logger.error(f"Error in stream_query: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": str(e)
            }

    def query(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the codebase with semantic search.
        
        Args:
            message: User's question about the code
            history: Previous conversation history
            filters: Optional filters (language, directory, etc.)
            
        Returns:
            Dict with response, code references, and metadata
        """
        # Ensure service is initialized
        if not self._ensure_initialized():
            return {
                "response": (
                    "[ERRO] **Serviço RAG não disponível**\n\n"
                    "O índice de código não foi encontrado ou o serviço não pôde ser inicializado.\n\n"
                    "**Possíveis causas:**\n"
                    "1. GEMINI_API_KEY não configurada\n"
                    "2. Dependências faltando (llama-index, faiss)\n"
                    "3. Índice não gerado (execute `python scripts/index_codebase.py`)\n\n"
                    "Verifique os logs para mais detalhes."
                ),
                "code_references": [],
                "metadata": {
                    "response_time": 0,
                    "sources_count": 0,
                    "error": "Service not initialized"
                }
            }
        
        try:
            start_time = datetime.now()
            
            # Build context from history if provided
            context_messages = []
            if history:
                for msg in history[-5:]:  # Last 5 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    context_messages.append(f"{role}: {content}")
            
            # Construct query with context
            full_query = message
            if context_messages:
                context_str = "\n".join(context_messages)
                full_query = f"Contexto da conversa:\n{context_str}\n\nPergunta atual: {message}"
            
            # Query the RAG engine
            logger.info(f"[QUERY] Querying codebase: {message[:100]}...")
            response = self._query_engine.query(full_query)
            
            # Extract source nodes (code references)
            code_references = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes[:5]:  # Top 5 sources
                    metadata = node.node.metadata
                    code_references.append({
                        "file": metadata.get("file_path", "unknown"),
                        "score": node.score,
                        "content": node.node.text[:500],  # First 500 chars
                        "lines": str(metadata.get("lines", "")),  # Convert to string
                    })
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "response": str(response),
                "code_references": code_references,
                "metadata": {
                    "response_time": round(response_time, 2),
                    "sources_count": len(code_references),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error querying codebase: {e}", exc_info=True)
            return {
                "response": f"[ERRO] **Erro ao processar consulta**\n\n{str(e)}",
                "code_references": [],
                "metadata": {
                    "response_time": 0,
                    "sources_count": 0,
                    "error": str(e)
                }
            }


# Singleton instance
_code_rag_service: Optional[CodeRAGService] = None


def get_code_rag_service() -> CodeRAGService:
    """
    Get or create the singleton CodeRAGService instance.
    
    Returns:
        CodeRAGService instance
    """
    global _code_rag_service
    if _code_rag_service is None:
        _code_rag_service = CodeRAGService()
    return _code_rag_service
