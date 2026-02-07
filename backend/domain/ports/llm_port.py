"""
Port: LLMPort

Interface abstrata para comunicação com LLMs (Large Language Models).
Implementada por: GeminiAdapter, GroqAdapter

Uso:
    from backend.domain.ports import LLMPort
    
    class MyAdapter(LLMPort):
        async def generate(self, messages, tools=None):
            ...

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """
    Resposta de uma chamada ao LLM.
    
    Attributes:
        content: Conteúdo textual da resposta
        tool_calls: Lista de chamadas de ferramentas (se houver)
        finish_reason: Motivo do término (stop, tool_calls, length)
        usage: Estatísticas de uso (tokens)
        raw_response: Resposta bruta do provider
    """
    
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None


@dataclass
class ToolDefinition:
    """
    Definição de uma ferramenta para o LLM.
    
    Attributes:
        name: Nome da ferramenta
        description: Descrição do que a ferramenta faz
        parameters: Schema JSON dos parâmetros
    """
    
    name: str
    description: str
    parameters: Dict[str, Any]


class LLMPort(ABC):
    """
    Interface abstrata para comunicação com LLMs.
    
    Esta é a porta principal para interação com modelos de linguagem.
    Implementações concretas devem ser criadas em infrastructure/adapters/llm/
    
    Example:
        >>> class GeminiAdapter(LLMPort):
        ...     async def generate(self, messages, tools=None):
        ...         # Implementação específica do Gemini
        ...         pass
    """
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Gera uma resposta a partir de uma lista de mensagens.
        
        Args:
            messages: Lista de mensagens no formato [{"role": "...", "content": "..."}]
            tools: Lista opcional de ferramentas disponíveis
            temperature: Temperatura de amostragem (0-1)
            max_tokens: Limite máximo de tokens na resposta
        
        Returns:
            LLMResponse com o conteúdo gerado
        
        Raises:
            LLMError: Em caso de erro na comunicação com o LLM
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        Gera uma resposta em streaming.
        
        Args:
            messages: Lista de mensagens
            tools: Lista opcional de ferramentas
            temperature: Temperatura de amostragem
        
        Yields:
            Chunks de texto conforme são gerados
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Retorna o nome do modelo sendo utilizado."""
        pass
    
    @abstractmethod
    def get_context_window(self) -> int:
        """Retorna o tamanho da janela de contexto do modelo."""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Conta o número de tokens em um texto.
        
        Args:
            text: Texto para contar tokens
        
        Returns:
            Número de tokens
        """
        pass
