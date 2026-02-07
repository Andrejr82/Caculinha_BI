"""
LLMCompressionAdapter — Adapter de Compressão via LLM

Autor: Backend Specialist Agent
Data: 2026-02-07
"""

from typing import List, Optional
import structlog

from backend.domain.ports.compression_port import ICompressionPort, CompressedContext
from backend.domain.entities.message import Message

logger = structlog.get_logger(__name__)


class LLMCompressionAdapter(ICompressionPort):
    """Adapter para compressão de contexto via LLM."""
    
    def __init__(self, llm_client=None, model: str = "gemini-2.5-flash-lite"):
        self.llm_client = llm_client
        self.model = model
    
    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4
    
    async def compress_messages(
        self, messages: List[Message], max_tokens: int = 2000, preserve_recent: int = 3
    ) -> CompressedContext:
        if not messages:
            return CompressedContext("", 0, 0, 1.0, [])
        
        original_tokens = sum(m.token_estimate for m in messages)
        if original_tokens <= max_tokens:
            return CompressedContext("", original_tokens, original_tokens, 1.0, messages)
        
        preserved = messages[-preserve_recent:]
        to_compress = messages[:-preserve_recent] if len(messages) > preserve_recent else []
        summary = await self.summarize_conversation(to_compress) if to_compress else ""
        compressed = self._estimate_tokens(summary) + sum(m.token_estimate for m in preserved)
        
        return CompressedContext(summary, original_tokens, compressed, compressed/original_tokens, preserved)
    
    async def summarize_conversation(self, messages: List[Message], focus: Optional[str] = None) -> str:
        if not messages:
            return ""
        formatted = "\n".join(f"{m.role}: {m.content}" for m in messages)
        if not self.llm_client:
            return formatted[:500]
        try:
            prompt = f"Resuma: {formatted}"
            return await self.llm_client.generate(prompt, max_tokens=300)
        except:
            return formatted[:500]
    
    async def extract_key_points(self, messages: List[Message], max_points: int = 5) -> List[str]:
        return [m.content[:100] for m in messages[:max_points]]
    
    async def should_compress(self, messages: List[Message], threshold_tokens: int = 4000) -> bool:
        return sum(m.token_estimate for m in messages) > threshold_tokens
    
    async def incremental_compress(self, existing_summary: str, new_messages: List[Message]) -> str:
        new_text = "\n".join(m.content[:100] for m in new_messages)
        return f"{existing_summary}\n{new_text}"
