
import os
import logging
import json
from typing import List, Dict, Any, Optional
from groq import Groq
from backend.app.core.llm_base import BaseLLMAdapter
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class GroqLLMAdapter(BaseLLMAdapter):
    """
    Adaptador para Groq Cloud API.
    Utiliza modelos Llama 3 para inferência ultra-rápida.
    """

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, system_instruction: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.provider = "groq"
        
        api_key = api_key or settings.GROQ_API_KEY
        if not api_key:
            # Fallback para variável de ambiente direta se não estiver no settings
            api_key = os.environ.get("GROQ_API_KEY")
            
        if not api_key:
            raise ValueError("GROQ_API_KEY não configurada")

        self.client = Groq(api_key=api_key)
        self.model_name = model_name or settings.GROQ_MODEL_NAME or "llama-3.3-70b-versatile"
        self.system_instruction = system_instruction
        self.max_output_tokens = settings.LLM_MAX_OUTPUT_TOKENS if settings.DEV_FAST_MODE else max(settings.LLM_MAX_OUTPUT_TOKENS, 1024)
        
        self.logger.info(f"[OK] GroqLLMAdapter inicializado: {self.model_name}")

    def get_capabilities(self) -> BaseLLMAdapter.Capabilities:
        return BaseLLMAdapter.Capabilities(
            chat=True,
            tools=True,
            streaming=False,
            json_mode=False,
        )

    def get_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """
        Obtém completion da Groq API.
        Compatível com o formato OpenAI/Gemini do projeto.
        """
        try:
            # Injetar instrução de sistema se fornecida
            if self.system_instruction:
                # Se a primeira mensagem já for system, atualiza, senão insere
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] = self.system_instruction
                else:
                    messages.insert(0, {"role": "system", "content": self.system_instruction})

            # Converter ferramentas para formato Groq (OpenAI-like)
            groq_tools = None
            tool_choice = None
            
            if tools:
                groq_tools = self._convert_tools(tools)
                if groq_tools:
                   tool_choice = "auto"

            # Prepare arguments
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": self.max_output_tokens,
                "top_p": 1,
                "stream": False
            }
            
            if groq_tools:
                kwargs["tools"] = groq_tools
                kwargs["tool_choice"] = tool_choice

            # Normalize messages (Gemini -> OpenAI format)
            normalized_messages = self._normalize_messages(messages)
            kwargs["messages"] = normalized_messages

            response = self.client.chat.completions.create(**kwargs)

            message = response.choices[0].message
            result = {"content": message.content or ""}

            if message.tool_calls:
                tool_calls = []
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
                result["tool_calls"] = tool_calls

            return result

        except Exception as e:
            self.logger.error(f"[ERR] Erro ao chamar Groq: {e}", exc_info=True)
            return {"error": str(e)}

    def _normalize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converte mensagens do formato interno (Gemini-like) para formato OpenAI/Groq.
        Principalmente: role 'model' -> 'assistant'.
        """
        normalized = []
        for msg in messages:
            new_msg = msg.copy()
            role = new_msg.get("role")
            
            # Map roles
            if role == "model":
                new_msg["role"] = "assistant"
            elif role == "function":
                # Convert 'function' role to 'tool' role for Groq/Llama-3
                new_msg["role"] = "tool"
                
                # Remove deprecated 'function_call' property if present in tool response
                if "function_call" in new_msg:
                    del new_msg["function_call"]
                
                # Ensure tool_call_id exists (required for tool role)
                if "tool_call_id" not in new_msg:
                    # Try to retrieve it from metadata or generate a placeholder
                    # Ideally this should match the request's tool_call_id, but for legacy compatibility
                    # we might need to fake it if lost.
                    # Check if 'name' is available to generate a somewhat unique ID
                    func_name = new_msg.get("name", "unknown")
                    new_msg["tool_call_id"] = f"call_{func_name}_legacy" 

            # Handle tool_calls structure (in assistant messages)
            if "tool_calls" in new_msg:
                # Ensure tool calls are correctly formatted
                # Our agent uses a generic dict, ensure it matches OpenAI format
                tcs = new_msg["tool_calls"]
                valid_tcs = []
                for tc in tcs:
                    if isinstance(tc, dict):
                         # Ensure 'function' key exists
                         if "function" in tc:
                             valid_tcs.append(tc)
                new_msg["tool_calls"] = valid_tcs
            
            # Remove keys that Groq doesn't like in general
            if "function_call" in new_msg and new_msg["role"] != "tool":
                 # If role is NOT tool (e.g. assistant), but has both tool_calls and function_call, prefer tool_calls
                 if "tool_calls" in new_msg:
                    del new_msg["function_call"]
            
            normalized.append(new_msg)
        return normalized

    async def generate_response(self, prompt: str) -> str:
        """Wrapper para compatibilidade com o endpoint de insights"""
        messages = [{"role": "user", "content": prompt}]
        result = self.get_completion(messages)
        if "error" in result:
            raise Exception(result["error"])
        return result.get("content", "")

    def invoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """Implementação do protocolo LangChain Runnable"""
        from langchain_core.messages import AIMessage
        
        if isinstance(input, str):
            messages = [{"role": "user", "content": input}]
        elif isinstance(input, list):
            # Converter de objetos LangChain para dicts
            messages = []
            for msg in input:
                role = "assistant" if hasattr(msg, "type") and msg.type == "ai" else "user"
                content = msg.content if hasattr(msg, "content") else str(msg)
                messages.append({"role": role, "content": content})
        else:
            messages = [{"role": "user", "content": str(input)}]

        result = self.get_completion(messages)
        if "error" in result:
            raise ValueError(result["error"])
            
        return AIMessage(content=result.get("content", ""))

    def get_llm(self):
        """Retorna self para compatibilidade com a fábrica de agentes"""
        return self

    def _convert_tools(self, tools_wrapper: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Converte o formato interno de ferramentas para o formato Groq/OpenAI"""
        function_declarations = tools_wrapper.get("function_declarations", [])
        groq_tools = []
        for fd in function_declarations:
            groq_tools.append({
                "type": "function",
                "function": {
                    "name": fd.get("name"),
                    "description": fd.get("description"),
                    "parameters": fd.get("parameters")
                }
            })
        return groq_tools
