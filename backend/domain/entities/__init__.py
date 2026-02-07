"""
Domain Entities — Exportação de Entidades

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from backend.domain.entities.conversation import Conversation
from backend.domain.entities.message import Message, MessageRole
from backend.domain.entities.memory_entry import MemoryEntry
from backend.domain.entities.document import Document, DocumentSource
from backend.domain.entities.embedding import Embedding
from backend.domain.entities.feature import Feature, FeatureValue


__all__ = [
    # Entities
    "Conversation",
    "Message",
    "MemoryEntry",
    "Document",
    "Embedding",
    "Feature",
    # Types
    "MessageRole",
    "DocumentSource",
    "FeatureValue",
]
