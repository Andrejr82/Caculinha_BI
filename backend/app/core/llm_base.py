from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class BaseLLMAdapter(ABC):
    @dataclass(frozen=True)
    class Capabilities:
        chat: bool = True
        tools: bool = False
        streaming: bool = False
        json_mode: bool = False

    provider: str = "unknown"
    model_name: str = ""

    def get_capabilities(self) -> "BaseLLMAdapter.Capabilities":
        return BaseLLMAdapter.Capabilities()

    @abstractmethod
    def get_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pass
