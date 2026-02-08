"""
LLM Adapter for Google GenAI SDK (Official - 2026)

Migrated from deprecated google-generativeai to google-genai.
Implements BaseLLMAdapter interface for compatibility with CaculinhaBIAgent.

Key Changes:
- Uses `from google import genai` instead of `import google.generativeai`
- Client-based API: `client = genai.Client(api_key=...)`
- Updated model names: gemini-2.5-pro (recommended), gemini-2.0-flash-exp (experimental)
"""

from typing import List, Dict, Any, Optional
import logging
import time
import json
from backend.app.core.llm_base import BaseLLMAdapter
from backend.app.config.settings import settings

GENAI_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Erro de importação do google-genai: {e}")
    print("Execute: pip install google-genai>=1.60.0")


class GenAILLMAdapter(BaseLLMAdapter):
    """
    Adaptador para Google GenAI SDK (oficial 2026).
    Substitui GeminiLLMAdapter (deprecated).
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        system_instruction: Optional[str] = None
    ):
        self.logger = logging.getLogger(__name__)

        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai não está instalado. "
                "Execute: pip install google-genai>=1.60.0"
            )

        # API Key
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada no arquivo .env")

        # Model Name
        raw_model_name = model_name or settings.LLM_MODEL_NAME or "gemini-2.5-pro"
        # Sanitização robusta para corrigir erros de .env com aspas ou comentários
        self.model_name = raw_model_name.split("#")[0].strip().replace('"', '').replace("'", "")
        
        # Client Initialization (NEW SDK PATTERN)
        self.client = genai.Client(api_key=self.api_key)
        
        # Configuration
        self.max_retries = 5
        self.retry_delay = 2.0
        self.system_instruction = system_instruction

        self.logger.info(f"[OK] GenAI adapter inicializado com modelo: {self.model_name}")

    def get_completion(self, messages: List[Dict[str, str]], tools: Optional[List] = None) -> Dict[str, Any]:
        """
        Gera completion usando novo SDK.
        
        Args:
            messages: Lista de mensagens no formato [{"role": "user/model", "content": str}]
            tools: Lista de ferramentas (function calling)
        
        Returns:
            {"content": str, "tool_calls": [...]} ou {"error": str}
        """
        for attempt in range(self.max_retries):
            try:
                # Convert messages to GenAI format
                genai_messages = self._convert_messages(messages)
                
                # Build request config
                # Build request config using GenerateContentConfig
                # FIX 2026-01-24: New SDK requires 'config' parameter object
                generate_config = types.GenerateContentConfig()
                
                if self.system_instruction:
                    generate_config.system_instruction = self.system_instruction
                
                if tools:
                    converted_tools = self._convert_tools(tools)
                    self.logger.info(f"DEBUG TOOLS: Original count: {len(tools) if hasattr(tools, '__len__') else '?'}, Converted: {len(converted_tools)}")
                    
                    # 🔴 DEBUG: Salvar ferramentas em arquivo
                    if converted_tools:
                        import json
                        from pathlib import Path
                        from datetime import datetime
                        
                        debug_dir = Path("debug_llm_responses")
                        debug_dir.mkdir(exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        tools_file = debug_dir / f"tools_{timestamp}.json"
                        
                        # Tentar serializar as ferramentas
                        try:
                            tools_dict = {
                                "timestamp": timestamp,
                                "original_tools_type": str(type(tools)),
                                "original_tools_str": str(tools)[:5000],  # Limitar tamanho
                                "converted_tools_count": len(converted_tools),
                                "converted_tools": []
                            }
                            
                            for i, tool in enumerate(converted_tools):
                                tool_info = {
                                    "index": i,
                                    "type": str(type(tool)),
                                    "str": str(tool)[:2000],  # Limitar
                                    "repr": repr(tool)[:2000],
                                }
                                
                                # Tentar extrair function_declarations se for um Tool
                                if hasattr(tool, 'function_declarations'):
                                    tool_info["has_function_declarations"] = True
                                    tool_info["function_declarations_count"] = len(tool.function_declarations)
                                    tool_info["function_declarations"] = []
                                    
                                    for j, func_decl in enumerate(tool.function_declarations):
                                        func_info = {
                                            "index": j,
                                            "type": str(type(func_decl)),
                                            "str": str(func_decl)[:1000],
                                        }
                                        
                                        if hasattr(func_decl, 'name'):
                                            func_info["name"] = func_decl.name
                                        if hasattr(func_decl, 'description'):
                                            func_info["description"] = func_decl.description
                                        if hasattr(func_decl, 'parameters'):
                                            func_info["parameters_type"] = str(type(func_decl.parameters))
                                            func_info["parameters_str"] = str(func_decl.parameters)[:500]
                                        
                                        tool_info["function_declarations"].append(func_info)
                                
                                tools_dict["converted_tools"].append(tool_info)
                            
                            with open(tools_file, 'w', encoding='utf-8') as f:
                                json.dump(tools_dict, f, indent=2, ensure_ascii=False)
                            
                            print(f"\n{'='*80}\n[DEBUG] Ferramentas salvas em: {tools_file}\n{'='*80}\n", flush=True)
                            self.logger.info(f"[DEBUG] Ferramentas salvas em: {tools_file}")
                        except Exception as e:
                            self.logger.error(f"Erro ao salvar ferramentas: {e}")
                    
                    if converted_tools:
                        generate_config.tools = converted_tools
                        # Explicitly set mode to AUTO only if tools exist
                        generate_config.tool_config = types.ToolConfig(
                            function_calling_config=types.FunctionCallingConfig(
                                mode="AUTO"
                            )
                        )
                
                # Call API
                self.logger.info(f"[DEBUG] Chamando GenAI SDK (tentativa {attempt + 1}/{self.max_retries})")
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=genai_messages,
                    config=generate_config
                )
                
                # Parse response
                return self._parse_response(response)
                
            except Exception as e:
                self.logger.warning(f"Erro na tentativa {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    return {"error": f"Falha após {self.max_retries} tentativas: {str(e)}"}
        
        return {"error": "Max retries exceeded"}

    async def generate_response(self, prompt: str) -> str:
        """Wrapper assíncrono para compatibilidade."""
        messages = [{"role": "user", "content": prompt}]
        result = self.get_completion(messages)
        
        if "error" in result:
            raise Exception(result["error"])
        
        return result.get("content", "")

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        **kwargs
    ) -> str:
        """Gera resposta com histórico."""
        original_instruction = self.system_instruction
        
        try:
            if system_instruction:
                self.system_instruction = system_instruction
            
            result = self.get_completion(messages)
            
            if "error" in result:
                raise Exception(result["error"])
            
            return result.get("content", "")
        finally:
            self.system_instruction = original_instruction

    def get_llm(self):
        """Retorna self para compatibilidade com LangChain."""
        self.logger.info("get_llm() chamado - retornando adapter nativo")
        return self

    def invoke(self, input: Any, config: Optional[Dict] = None) -> Any:
        """LangChain Runnable protocol."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        from langchain_core.prompt_values import ChatPromptValue

        messages = []
        if isinstance(input, ChatPromptValue):
            messages = input.to_messages()
        elif isinstance(input, list):
            messages = input
        elif isinstance(input, str):
            messages = [HumanMessage(content=input)]
        
        # Convert to adapter format
        adapter_messages = []
        for msg in messages:
            role = "user"
            if hasattr(msg, "__class__"):
                if msg.__class__.__name__ == "AIMessage":
                    role = "model"
            
            content = msg.content if hasattr(msg, "content") else str(msg)
            adapter_messages.append({"role": role, "content": content})
        
        result = self.get_completion(adapter_messages)
        
        if "error" in result:
            raise ValueError(result["error"])
        
        return AIMessage(content=result.get("content", ""))

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Dict]:
        """Converte mensagens para formato GenAI (com suporte a Function Calling)."""
        converted = []
        # Lazy import para evitar problemas se sdk não instalado (embora verificado no init)
        try:
            from google.genai import types
        except ImportError:
            self.logger.error("google.genai.types não disponível em _convert_messages")
            return []
            
        import json

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content")
            
            # --- Handle Tool Calls (Assistant -> Model) ---
            if "tool_calls" in msg:
                # É uma mensagem do modelo pedindo execução de ferramenta
                parts = []
                for tc in msg["tool_calls"]:
                    # Suporte robusto a diferentes estruturas de tool_call
                    func = tc.get("function", {})
                    func_name = func.get("name")
                    raw_args = func.get("arguments", {})
                    
                    if not func_name:
                        continue
                        
                    # Argumentos podem vir como dict ou string JSON
                    args = raw_args
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except:
                            self.logger.warning(f"Falha ao parsear argumentos JSON para {func_name}: {raw_args}")
                            pass
                            
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(
                                name=func_name,
                                args=args
                            )
                        )
                    )
                
                if parts:
                    converted.append({
                        "role": "model",
                        "parts": parts
                    })
                continue

            # --- Handle Tool Response (Function -> User) ---
            if role in ["function", "tool"]:
                # É o resultado de uma ferramenta
                # No formato Google v1, tool responses são parts de role 'user'
                func_name = msg.get("name", "unknown_tool")
                
                # Content deve ser transformado em dict para o SDK
                response_data = {"result": content} # Default wrapper
                
                if content is None:
                    response_data = {"result": "No content"}
                elif isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                        # SDK exige dict como response content
                        if isinstance(parsed, dict):
                            response_data = parsed
                        else:
                            response_data = {"result": parsed}
                    except:
                        # Se não for JSON válido, manda como string crua envelopada
                        pass
                elif isinstance(content, dict):
                     response_data = content
                
                part = types.Part(
                    function_response=types.FunctionResponse(
                        name=func_name,
                        response=response_data
                    )
                )
                
                converted.append({
                    "role": "user",
                    "parts": [part]
                })
                continue

            # --- Handle Standard Text Messages ---
            # GenAI uses "user" and "model" (not "assistant")
            if role == "assistant":
                role = "model"
            
            # Tratamento para content nulo (pode acontecer em tool calls mal formatados)
            text_content = str(content) if content is not None else ""
            
            # MERGE LOGIC 2026: Merge consecutive user messages to avoid API errors
            # (Context Fencing + Schema Injection creates multiple user messages)
            if converted and converted[-1]["role"] == role and role == "user":
                # Check if previous message is text-based (has 'parts' with 'text')
                prev_parts = converted[-1]["parts"]
                # Only merge if the last part is text (not function call/response)
                # Google V1 SDK parts are objects, checking if it has text field
                last_part = prev_parts[-1]
                
                # Check if it's a text part (has text attribute or key)
                is_text_part = False
                if isinstance(last_part, dict) and "text" in last_part:
                    is_text_part = True
                elif hasattr(last_part, "text") and last_part.text:
                    is_text_part = True
                    
                if is_text_part:
                    # Append text to previous message with a newline separator
                    if isinstance(last_part, dict):
                        last_part["text"] += "\n\n" + text_content
                    else:
                        # Recreate part if it's an object (immutable sometimes?)
                        # Assuming we can modify it or append a new text part
                        # Better: Append a NEW text part to the same message
                        prev_parts.append({"text": text_content})
                    continue

            converted.append({
                "role": role,
                "parts": [{"text": text_content}]
            })
            
        return converted

    def _convert_tools(self, tools: Any) -> List[Any]:
        """Converte ferramentas para formato GenAI (GenerateContentConfig)."""
        # Extrair lista de declarações
        declarations = []
        
        if isinstance(tools, dict) and "function_declarations" in tools:
            declarations = tools["function_declarations"]
        elif isinstance(tools, list):
            declarations = tools
        
        if not declarations:
            return []
        
        # LIMPAR schemas para garantir compatibilidade com Gemini
        cleaned_declarations = []
        for decl in declarations:
            cleaned_decl = self._clean_tool_declaration(decl)
            cleaned_declarations.append(cleaned_decl)
            
        # O novo SDK espera: tools=[types.Tool(function_declarations=[...])]
        try:
            from google.genai import types
            
            # Converter para FunctionDeclaration objects
            func_decls = []
            for decl in cleaned_declarations:
                try:
                    func_decl = types.FunctionDeclaration(
                        name=decl["name"],
                        description=decl.get("description", ""),
                        parameters=self._schema_to_genai(decl.get("parameters", {}))
                    )
                    func_decls.append(func_decl)
                except Exception as e:
                    self.logger.warning(f"Erro ao converter ferramenta {decl.get('name', '?')}: {e}")
            
            if not func_decls:
                return []
                
            tool_obj = types.Tool(function_declarations=func_decls)
            return [tool_obj]
            
        except ImportError:
            self.logger.warning("google.genai.types não disponível em _convert_tools")
            return []
        except Exception as e:
            self.logger.error(f"Erro ao converter tools: {e}")
            return []
    
    def _clean_tool_declaration(self, decl: dict) -> dict:
        """Limpa uma declaração de ferramenta para compatibilidade com Gemini."""
        cleaned = {
            "name": decl.get("name", "unknown"),
            "description": decl.get("description", "")
        }
        
        params = decl.get("parameters", {})
        if params:
            cleaned["parameters"] = self._clean_schema_deep(params)
        
        return cleaned
    
    def _clean_schema_deep(self, schema: dict) -> dict:
        """Limpeza profunda de schema JSON para Gemini."""
        if not isinstance(schema, dict):
            return schema
        
        result = {}
        
        # Remover chaves inválidas
        invalid_keys = {"title", "default", "additionalProperties", "$defs", "definitions"}
        
        for key, value in schema.items():
            if key in invalid_keys:
                continue
            
            # Tratar anyOf - pegar o tipo não-null
            if key == "anyOf":
                valid_opt = next((opt for opt in value if opt.get("type") != "null"), None)
                if valid_opt:
                    result.update(self._clean_schema_deep(valid_opt))
                else:
                    result["type"] = "string"
                continue
            
            # Recursão para properties
            if key == "properties" and isinstance(value, dict):
                result[key] = {k: self._clean_schema_deep(v) for k, v in value.items()}
            elif key == "items" and isinstance(value, dict):
                result[key] = self._clean_schema_deep(value)
            else:
                result[key] = value
        
        return result
    
    def _schema_to_genai(self, schema: dict):
        """Converte schema dict para types.Schema do Gemini."""
        from google.genai import types
        
        if not schema:
            return None
        
        schema_type = schema.get("type", "object").upper()
        
        # Mapear tipos
        type_map = {
            "STRING": types.Type.STRING,
            "INTEGER": types.Type.INTEGER,
            "NUMBER": types.Type.NUMBER,
            "BOOLEAN": types.Type.BOOLEAN,
            "ARRAY": types.Type.ARRAY,
            "OBJECT": types.Type.OBJECT,
        }
        
        genai_type = type_map.get(schema_type, types.Type.STRING)
        
        kwargs = {"type": genai_type}
        
        # Properties para OBJECT
        if "properties" in schema:
            kwargs["properties"] = {
                k: self._schema_to_genai(v) for k, v in schema["properties"].items()
            }
        
        # Items para ARRAY
        if "items" in schema:
            kwargs["items"] = self._schema_to_genai(schema["items"])
        
        # Required
        if "required" in schema:
            kwargs["required"] = schema["required"]
        
        # Description
        if "description" in schema:
            kwargs["description"] = schema["description"]
        
        return types.Schema(**kwargs)

    def _parse_response(self, response) -> Dict[str, Any]:
        """Parse resposta da API."""
        try:
            # 🔴 DEBUG: Salvar resposta RAW em arquivo para análise
            import json
            from pathlib import Path
            from datetime import datetime
            
            debug_dir = Path("debug_llm_responses")
            debug_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = debug_dir / f"response_{timestamp}.json"
            
            # Converter response para dict serializável
            response_dict = {
                "timestamp": timestamp,
                "has_candidates": hasattr(response, 'candidates'),
                "candidates_count": len(response.candidates) if hasattr(response, 'candidates') else 0,
                "raw_response_str": str(response),
                "raw_response_repr": repr(response),
                "response_type": str(type(response)),
            }
            
            # Tentar extrair mais detalhes
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                response_dict["candidate_0"] = {
                    "has_content": hasattr(candidate, 'content'),
                    "content_str": str(candidate.content) if hasattr(candidate, 'content') else None,
                    "content_repr": repr(candidate.content) if hasattr(candidate, 'content') else None,
                }
                
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    response_dict["candidate_0"]["parts_count"] = len(candidate.content.parts)
                    response_dict["candidate_0"]["parts"] = []
                    
                    for i, part in enumerate(candidate.content.parts):
                        part_info = {
                            "index": i,
                            "type": str(type(part)),
                            "str": str(part),
                            "repr": repr(part),
                            "dir": dir(part),
                            "has_text": hasattr(part, 'text'),
                            "has_function_call": hasattr(part, 'function_call'),
                            "has_function_response": hasattr(part, 'function_response'),
                        }
                        
                        if hasattr(part, 'text'):
                            part_info["text_value"] = part.text
                        if hasattr(part, 'function_call'):
                            part_info["function_call_str"] = str(part.function_call)
                        
                        response_dict["candidate_0"]["parts"].append(part_info)
            
            # Salvar em arquivo
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(response_dict, f, indent=2, ensure_ascii=False)
            
            print(f"\n{'='*80}\n[DEBUG] Resposta RAW salva em: {debug_file}\n{'='*80}\n", flush=True)
            self.logger.info(f"[DEBUG] Resposta RAW salva em: {debug_file}")
            
            # Continuar com parsing normal
            tool_calls = []
            content_text = ""

            # DEBUG: Log raw response structure (simplified)
            # self.logger.debug(f"Raw Response: {response}")

            content_text = ""
            tool_calls = []
            
            # 1. Check for Safety Blocks / Empty Candidates
            if not getattr(response, "candidates", None):
                 problem = "Sem candidatos gerados."
                 if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                      if getattr(response.prompt_feedback, "block_reason", None):
                           problem = f"Bloqueio de Segurança: {response.prompt_feedback.block_reason}"
                 
                 self.logger.error(f"[ERROR] Erro na geração: {problem}")
                 return {"error": problem}

            candidate = response.candidates[0]
            
            # 2. Extract Parts (Text and Tool Calls)
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                for part in candidate.content.parts:
                    # 1. Extract Text
                    if hasattr(part, "text") and part.text:
                        content_text += part.text
                    
                    # 2. Extract Function Calls
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        
                        # Handle args extraction safely
                        args = fc.args
                        # The SDK dictates args is a dict/map, sometimes wrapped
                        if hasattr(args, "to_dict"): 
                            args = args.to_dict()
                        elif hasattr(args, "_asdict"):
                            args = args._asdict() # NamedTuple support
                        
                        tool_calls.append({
                            "id": f"call_{fc.name}_{int(time.time()*1000)}", 
                            "type": "function",
                            "function": {
                                "name": fc.name,
                                "arguments": json.dumps(args) if isinstance(args, (dict, list)) else str(args)
                            }
                        })

            # 3. Fallback: Direct text attribute
            if not content_text and not tool_calls and hasattr(response, "text") and response.text:
                 content_text = response.text

            # 4. Log Usage (Token Counts)
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                 self.logger.info(f"[DATA] Usage: {response.usage_metadata}")

            # Return success results
            if tool_calls:
                self.logger.info(f"[OK] Tool calls detectados: {[t['function']['name'] for t in tool_calls]}")
                return {"content": content_text, "tool_calls": tool_calls}
            
            if content_text:
                self.logger.info(f"[OK] Resposta extraída via parts/text: {content_text[:100]}...")
                return {"content": content_text}
            
            # If still empty but no error detected
            self.logger.error(f"[ERROR] Resposta vazia detectada (mas com candidatos).")
            print(f"\n{'='*80}\n[CRITICAL DEBUG] RESPOSTA VAZIA DO LLM!\n{'='*80}\n", flush=True)
            self.logger.error(f"[DEBUG] Response object: {response}")
            self.logger.error(f"[DEBUG] Candidates: {getattr(response, 'candidates', 'NO ATTR')}")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                self.logger.error(f"[DEBUG] Candidate content: {getattr(candidate, 'content', 'NO ATTR')}")
                if hasattr(candidate, 'content'):
                    self.logger.error(f"[DEBUG] Content parts: {getattr(candidate.content, 'parts', 'NO ATTR')}")
                    if hasattr(candidate.content, 'parts'):
                        for i, part in enumerate(candidate.content.parts):
                            self.logger.error(f"[DEBUG] Part {i}: {part}")
                            self.logger.error(f"[DEBUG] Part {i} attributes: {dir(part)}")
            return {"error": "Resposta vazia da API (Conteúdo nulo)"}
            
        except Exception as e:
            self.logger.error(f"[ERROR] Erro crítico ao parsear resposta: {e}", exc_info=True)
            return {"error": f"Erro crítico na resposta do LLM: {str(e)}"}
