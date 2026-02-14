"""
Legacy pipeline factory compatibility layer for feedback endpoint/tests.
"""

from __future__ import annotations

from dataclasses import dataclass


class _MemoryAgent:
    async def save_feedback(self, request_id: str, rating: int, comment: str | None = None) -> bool:
        return True


@dataclass
class _PipelineFactory:
    def get_memory_agent(self) -> _MemoryAgent:
        return _MemoryAgent()


def get_pipeline_factory() -> _PipelineFactory:
    return _PipelineFactory()

