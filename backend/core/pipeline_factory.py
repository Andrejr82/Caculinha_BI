"""
Legacy pipeline factory compatibility layer for feedback endpoint/tests.

This module is still used by the legacy `/api/v1/feedback` route. Instead of
returning a fake in-memory agent, it now creates a real `MemoryAgent` backed by
the SQLite chat-state database so the compatibility route persists feedback.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.application.agents.memory_agent import MemoryAgent
from backend.app.core.utils.session_manager import SessionManager
from backend.infrastructure.adapters.sqlite_memory_adapter import SQLiteMemoryAdapter


@dataclass
class _PipelineFactory:
    _memory_agent: MemoryAgent | None = field(default=None, init=False, repr=False)

    def get_memory_agent(self) -> MemoryAgent:
        if self._memory_agent is None:
            adapter = SQLiteMemoryAdapter(str(SessionManager.default_db_path()))
            self._memory_agent = MemoryAgent(adapter)
        return self._memory_agent


_PIPELINE_FACTORY = _PipelineFactory()


def get_pipeline_factory() -> _PipelineFactory:
    return _PIPELINE_FACTORY

