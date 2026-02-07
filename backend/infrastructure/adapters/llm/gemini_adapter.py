"""
GeminiAdapter - Adapter para Google Gemini

Implementa LLMPort para comunicação real com Google Gemini API.

Uso:
    from backend.infrastructure.adapters.llm import GeminiAdapter
    
    adapter = GeminiAdapter()
    response = await adapter.generate(messages)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

import os
from typing import List, Dict, Any, Optional, AsyncIterator

import structlog
from google import genai
from google.genai import types

from backend.domain.ports.llm_port import LLMPort, LLMResponse, ToolDefinition


logger = structlog.get_logger(__name__)


class GeminiAdapter(LLMPort):
    """
    Adapter real para Google Gemini API.
    
    Implementa LLMPort usando a biblioteca google-genai.
    Configurado para gemini-2.5-pro conforme .env do projeto.
    
    Example:
        >>> adapter = GeminiAdapter()
        >>> response = await adapter.generate([
        ...     {"role": "user", "content": "Olá"}
        ... ])
        >>> print(response.content)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-pro",
    ):
        """
        Inicializa o GeminiAdapter.
        
        Args:
            api_key: Chave da API (usa GEMINI_API_KEY ou GOOGLE_API_KEY do ambiente)
            model_name: Nome do modelo (padrão: gemini-2.5-pro)
        """
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._model_name = model_name
        self._context_window = 1000000  # Gemini 2.5 Pro
        
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY ou GOOGLE_API_KEY não configurada")
        
        # Configurar cliente
        self._client = genai.Client(api_key=self._api_key)
        
        logger.info("gemini_adapter_initialized", model=self._model_name)
    
    def _normalize_messages(self, messages: List[Dict[str, Any]]) -> List[types.Content]:
        """Converte mensagens para formato Gemini."""
        contents = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Mapear roles
            if role in ("assistant", "model"):
                gemini_role = "model"
            else:
                gemini_role = "user"
            
            contents.append(types.Content(
                role=gemini_role,
                parts=[types.Part(text=content)]
            ))
        
        return contents
    
    def _convert_tools(self, tools: List[ToolDefinition]) -> List[types.Tool]:
        """Converte ferramentas para formato Gemini."""
        if not tools:
            return []
        
        function_declarations = []
        for tool in tools:
            function_declarations.append(types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters
            ))
        
        return [types.Tool(function_declarations=function_declarations)]
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Gera uma resposta usando Gemini.
        
        Args:
            messages: Lista de mensagens
            tools: Ferramentas disponíveis
            temperature: Temperatura (0-1)
            max_tokens: Limite de tokens
        
        Returns:
            LLMResponse com o conteúdo gerado
        """
        try:
            contents = self._normalize_messages(messages)
            gemini_tools = self._convert_tools(tools) if tools else None
            
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 8192,
            )
            
            if gemini_tools:
                config.tools = gemini_tools
            
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config,
            )
            
            # Extrair conteúdo
            content = ""
            tool_calls = []
            
            if response.candidates:
                candidate = response.candidates[0]
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        content += part.text
                    elif hasattr(part, "function_call") and part.function_call:
                        tool_calls.append({
                            "name": part.function_call.name,
                            "arguments": dict(part.function_call.args) if part.function_call.args else {},
                        })
            
            # Estatísticas de uso
            usage = None
            if response.usage_metadata:
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }
            
            logger.info(
                "gemini_generation_completed",
                content_length=len(content),
                tool_calls=len(tool_calls),
                tokens=usage.get("total_tokens") if usage else None,
            )
            
            return LLMResponse(
                content=content,
                tool_calls=tool_calls if tool_calls else None,
                finish_reason="tool_calls" if tool_calls else "stop",
                usage=usage,
                raw_response=response,
            )
            
        except Exception as e:
            logger.error("gemini_generation_error", error=str(e))
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """
        Gera uma resposta em streaming.
        
        Yields:
            Chunks de texto conforme são gerados
        """
        try:
            contents = self._normalize_messages(messages)
            
            config = types.GenerateContentConfig(
                temperature=temperature,
            )
            
            async for chunk in self._client.aio.models.generate_content_stream(
                model=self._model_name,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error("gemini_stream_error", error=str(e))
            raise
    
    def get_model_name(self) -> str:
        """Retorna o nome do modelo."""
        return self._model_name
    
    def get_context_window(self) -> int:
        """Retorna o tamanho da janela de contexto."""
        return self._context_window
    
    async def count_tokens(self, text: str) -> int:
        """
        Conta o número de tokens em um texto.
        
        Args:
            text: Texto para contar tokens
        
        Returns:
            Número de tokens
        """
        try:
            response = await self._client.aio.models.count_tokens(
                model=self._model_name,
                contents=[types.Content(parts=[types.Part(text=text)])]
            )
            return response.total_tokens
        except Exception as e:
            logger.warning("token_count_fallback", error=str(e))
            # Estimativa aproximada
            return len(text) // 4
