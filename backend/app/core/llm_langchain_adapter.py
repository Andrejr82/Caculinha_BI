# core/llm_langchain_adapter.py
from typing import Any, List, Optional, Dict
import json
import logging

from app.core.llm_base import BaseLLMAdapter

logger = logging.getLogger(__name__)

LANGCHAIN_AVAILABLE = False
try:
    from langchain_core.callbacks import CallbackManagerForLLMRun
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import (
        BaseMessage,
        AIMessage,
        HumanMessage,
        SystemMessage,
        FunctionMessage,
        ToolMessage,
        ToolCall,
        AIMessageChunk,
    )
    from langchain_core.outputs import (
        ChatResult,
        ChatGeneration,
        ChatGenerationChunk,
    )
    LANGCHAIN_AVAILABLE = True
except (ImportError, OSError):
    # Dummy classes for safe import
    BaseChatModel = object
    CallbackManagerForLLMRun = Any
    BaseMessage = Any
    ChatResult = Any
    logger.warning("LangChain dependencies missing. CustomLangChainLLM will be disabled.")


def _clean_json_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove a chave 'anyOf' de um dicionário JSON Schema, recursivamente.
    A API Gemini não suporta 'anyOf' diretamente.
    """
    cleaned_schema = {}
    for key, value in schema.items():
        if key == "anyOf":
            # Ignorar 'anyOf' completamente
            continue
        elif isinstance(value, dict):
            cleaned_schema[key] = _clean_json_schema(value)
        elif isinstance(value, list):
            cleaned_list = []
            for item in value:
                if isinstance(item, dict):
                    cleaned_list.append(_clean_json_schema(item))
                else:
                    cleaned_list.append(item)
            cleaned_schema[key] = cleaned_list
        else:
            cleaned_schema[key] = value
    return cleaned_schema


class CustomLangChainLLM(BaseChatModel):
    llm_adapter: Any # Allow SmartLLM (Duck Typing)
    tools: Optional[List[Any]] = None # Adicionado para permitir o campo 'tools'

    @property
    def _llm_type(self) -> str:
        return "custom_llm"

    def __init__(self, llm_adapter: BaseLLMAdapter, **kwargs: Any):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is not available.")
        super().__init__(llm_adapter=llm_adapter, **kwargs)

    def bind_tools(
        self,
        tools: List[Any],
        **kwargs: Any,
    ) -> "CustomLangChainLLM":
        """Bind tools to the model."""
        if not LANGCHAIN_AVAILABLE:
             raise ImportError("LangChain is not available.")
             
        new_instance = self.__class__(llm_adapter=self.llm_adapter, **kwargs)
        new_instance.tools = tools  # Store tools for _generate to access
        return new_instance

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not LANGCHAIN_AVAILABLE:
             raise ImportError("LangChain is not available.")

        # Convert LangChain messages to a generic dictionary format
        # that GeminiLLMAdapter can understand (similar to OpenAI-like format)
        generic_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                generic_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                if msg.tool_calls:
                    processed_tool_calls = []
                    for tc in msg.tool_calls:
                        tc_dict = tc if isinstance(tc, dict) else tc.dict()
                        processed_tool_calls.append({
                            "id": tc_dict.get("id"),
                            "type": "function",
                            "function": {
                                "name": tc_dict.get("name"),
                                "arguments": json.dumps(tc_dict.get("args", {})),
                            },
                        })
                    generic_messages.append(
                        {
                            "role": "model",
                            "content": msg.content,
                            "tool_calls": processed_tool_calls,
                        }
                    )
                else:
                    generic_messages.append(
                        {"role": "model", "content": msg.content}
                    )
            elif isinstance(msg, SystemMessage):
                # Treat SystemMessage as a user message for Gemini
                generic_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, FunctionMessage):
                # FunctionMessage is typically a tool response in LangChain
                # Convert it to a user message with function_response for Gemini
                generic_messages.append(
                    {
                        "role": "user",
                        "function_call": { # This key is used by GeminiLLMAdapter to identify tool responses
                            "name": msg.name, # The name of the tool that was called
                            "response": {"content": str(msg.content)}
                        }
                    }
                )
            elif isinstance(msg, ToolMessage):
                # ToolMessage is also a tool response in LangChain
                # Convert it to a user message with function_response for Gemini

                # Extract tool name from ToolMessage
                tool_name = msg.name

                # Fallback: if name is empty, try to extract from tool_call_id
                if not tool_name or tool_name == "":
                    if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
                        # tool_call_id format is typically "call_<function_name>"
                        tool_name = msg.tool_call_id.replace("call_", "")
                    else:
                        # Last resort: use a default name
                        tool_name = "unknown_tool"

                generic_messages.append(
                    {
                        "role": "user", # Tool responses are part of the user's turn
                        "function_call": { # This key is used by GeminiLLMAdapter to identify tool responses
                            "name": tool_name,  # The name of the tool that was called
                            "response": {"content": str(msg.content)}
                        }
                    }
                )
            else:
                raise ValueError(f"Unsupported message type: {type(msg)}")

        # Check if tools were bound via bind_tools or passed directly in kwargs
        tools_to_pass = getattr(self, 'tools', None) or kwargs.get("tools")
        if tools_to_pass:
            generic_tools_declarations = []
            for tool in tools_to_pass:
                if hasattr(tool, 'name') and hasattr(tool, 'description') and hasattr(tool, 'args'):
                    # LangChain's StructuredTool has 'name', 'description', and 'args'
                    
                    # Infer required parameters
                    required_params = [
                        param for param, details in tool.args.items() 
                        if details.get("default") is None and details.get("type") != "null"
                    ]

                    # Create a copy of tool.args and remove 'default' if it's causing issues
                    processed_args = {}
                    for param, details in tool.args.items():
                        param_details = details.copy()
                        if "default" in param_details:
                            del param_details["default"] # Remover a chave 'default'
                        if "title" in param_details: # Remover a chave 'title'
                            del param_details["title"]
                        processed_args[param] = param_details

                    # Limpar o esquema de processed_args para remover 'anyOf'
                    cleaned_processed_args = _clean_json_schema(processed_args)

                    generic_tools_declarations.append(
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                "type": "object",
                                "properties": cleaned_processed_args, # Usar cleaned_processed_args
                                "required": required_params,
                            },
                        }
                    )
                elif isinstance(tool, dict) and "name" in tool and "description" in tool and "parameters" in tool:
                    # If it's already a dictionary in the expected function declaration format
                    generic_tools_declarations.append(tool)
                else:
                    # Fallback for other tool types or if the tool object is not fully formed
                    print(f"Warning: Unexpected tool format encountered: {type(tool)} - {tool}")
                    if hasattr(tool, 'name') and hasattr(tool, 'description'):
                         generic_tools_declarations.append(
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": {"type": "object", "properties": {}}, # Empty parameters
                                }
                        )
                    else:
                        raise ValueError(f"Unsupported tool object: {tool}")

            # Gemini API expects a single list of function declarations under a 'function_declarations' key
            tools_to_pass = {"function_declarations": generic_tools_declarations}
        else:
            tools_to_pass = None


        llm_response = self.llm_adapter.get_completion(
            messages=generic_messages, tools=tools_to_pass
        )

        if "error" in llm_response:
            raise Exception(f"LLM Adapter Error: {llm_response['error']}")

        content = llm_response.get("content") or ""
        tool_calls_data = llm_response.get("tool_calls")

        lc_tool_calls = []
        if tool_calls_data:
            for tc_data in tool_calls_data:
                try:
                    # tc_data is already a dictionary from GeminiLLMAdapter
                    args = json.loads(tc_data["function"]["arguments"])
                except (json.JSONDecodeError, TypeError):
                    args = {
                        "error": "Argumentos em formato JSON inválido",
                        "received": tc_data["function"]["arguments"],
                    }

                lc_tool_calls.append(
                    ToolCall(name=tc_data["function"]["name"], args=args, id=tc_data["id"])
                )

        ai_message = AIMessage(content=content, tool_calls=lc_tool_calls)

        return ChatResult(generations=[ChatGeneration(message=ai_message)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise NotImplementedError(
            "CustomLangChainLLM does not support async generation yet."
        )

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not LANGCHAIN_AVAILABLE:
             raise ImportError("LangChain is not available.")
             
        chat_result = self._generate(messages, stop, run_manager, **kwargs)
        generation = chat_result.generations[0]
        ai_message = generation.message

        message_chunk = AIMessageChunk(
            content=ai_message.content, tool_calls=ai_message.tool_calls
        )

        yield ChatGenerationChunk(message=message_chunk)
