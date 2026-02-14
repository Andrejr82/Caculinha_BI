import logging
import sys
from typing import Optional, List, Dict, Any
from backend.app.config.settings import settings
from backend.app.core.llm_groq_adapter import GroqLLMAdapter

logger = logging.getLogger(__name__)

# Legacy namespace compatibility for contract tests that patch "app.core.llm_factory".
sys.modules.setdefault("app.core.llm_factory", sys.modules[__name__])


class LLMFactory:
    """
    Fábrica inteligente para instanciar adaptadores de LLM.
    FIX 2026-01-09: Groq primário, Gemini fallback opcional.
    """
    
    @staticmethod
    def get_adapter(provider: Optional[str] = None, use_smart: bool = True):
        """
        Retorna um adaptador LLM com fallback automático.
        
        Args:
            provider: Provider específico ('google' ou 'groq'). Se None, usa settings.LLM_PROVIDER.
            use_smart: Se True, retorna SmartLLM com fallback automático.
        """
        # Respeitar configuração do .env (FIX 2026-01-16)
        provider = provider or settings.LLM_PROVIDER or "google"
        
        if use_smart:
            try:
                return SmartLLM(primary=provider)
            except Exception as e:
                logger.error(f"Falha ao criar SmartLLM: {e}. Usando adapter simples.")
        
        # Fallback para adapter simples - só Groq
        try:
            return GroqLLMAdapter()
        except Exception as e:
            logger.error(f"Falha ao iniciar Groq: {e}")
            raise


class SmartLLM:
    """
    Wrapper inteligente com fallback automático em tempo de execução.
    
    FIX 2026-01-09: Gemini é opcional - continua funcionando se API key expirada.
    """
    
    def __init__(self, primary: Optional[str] = None):
        # FIX 2026-02-04: Usar configuração do .env, com Google Gemini como padrão
        self.primary = primary or settings.LLM_PROVIDER or "google"
        self._groq = None  # Lazy init
        self._gemini = None  # Lazy init
        self.system_instruction = None  # Será setado pelo CaculinhaBIAgent
        self.dev_fast_mode = bool(getattr(settings, "DEV_FAST_MODE", False))
        
        # FIX DEFINITIVO 2026-01-09: Verificar se Gemini está disponível no startup
        # Só marca como disponível se API key existir e parecer válida
        gemini_key = getattr(settings, 'GEMINI_API_KEY', None) or ""
        self._gemini_available = bool(gemini_key and len(gemini_key) > 10 and "expired" not in gemini_key.lower())
        if self.dev_fast_mode and self.primary == "groq":
            # In dev-fast with Groq primary, disable Gemini fallback to avoid extra cost/noise.
            self._gemini_available = False
        
        if not self._gemini_available:
            logger.info("SmartLLM: Gemini desabilitado (sem API key válida). Usando apenas Groq.")
        
        logger.info(f"SmartLLM initialized: primary={self.primary}, gemini_available={self._gemini_available}")


    @property
    def groq(self):
        if self._groq is None:
            self._groq = GroqLLMAdapter()
        return self._groq
    
    @property
    def gemini(self):
        if self._gemini is None and self._gemini_available:
            try:
                # FIX 2026-01-24: Migrated to official google-genai SDK
                from backend.app.core.llm_genai_adapter import GenAILLMAdapter
                self._gemini = GenAILLMAdapter()
            except Exception as e:
                logger.warning(f"GenAI não disponível (API key expirada ou inválida): {e}")
                self._gemini_available = False
                return None
        return self._gemini

    def _is_rate_limit_error(self, error_str: str) -> bool:
        """Check if error indicates rate limiting"""
        error_lower = error_str.lower()
        return any(x in error_lower for x in ["429", "quota", "rate limit", "resource_exhausted"])

    def _is_payload_too_large_error(self, error_str: str) -> bool:
        error_lower = error_str.lower()
        return any(x in error_lower for x in ["413", "payload too large", "request too large", "tokens per minute"])

    def _sanitize_user_error(self, raw_error: str) -> str:
        err = (raw_error or "").lower()
        if self._is_rate_limit_error(err):
            return "Quota estourada / configure billing / tente depois."
        if self._is_payload_too_large_error(err):
            return "A consulta ficou grande demais para o fallback. Tente uma pergunta mais objetiva."
        return "Nao foi possivel concluir a analise agora. Tente novamente em instantes."

    def _compact_messages_for_fallback(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reduce payload size before fallback provider call (prevents Groq 413 TPM spikes).
        Keep system prompt and only the most recent conversational turns.
        """
        if not messages:
            return messages

        system_msgs = [m for m in messages if m.get("role") == "system"][:1]
        non_system = [m for m in messages if m.get("role") != "system"]
        tail = non_system[-6:]
        compacted: List[Dict[str, Any]] = []

        if system_msgs:
            system = dict(system_msgs[0])
            content = str(system.get("content", ""))
            if len(content) > 2500:
                system["content"] = content[:2500] + "\n\n[system truncated for fallback]"
            compacted.append(system)

        for msg in tail:
            item = dict(msg)
            if "content" in item and isinstance(item["content"], str) and len(item["content"]) > 3000:
                item["content"] = item["content"][:3000] + "\n\n[content truncated for fallback]"
            compacted.append(item)

        return compacted

    def _prepare_messages_for_primary(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.dev_fast_mode:
            return messages
        return self._compact_messages_for_fallback(messages)

    async def generate_response(self, prompt: str) -> str:
        """Async generation with fallback"""
        primary_adapter = self.groq if self.primary == "groq" else self.gemini
        
        # Se primário for Gemini mas não está disponível, usar Groq
        if primary_adapter is None:
            primary_adapter = self.groq
        
        try:
            return await primary_adapter.generate_response(prompt)
        except Exception as e:
            if self._is_rate_limit_error(str(e)) and self.gemini:
                logger.warning(f"Rate limit! Usando fallback Gemini...")
                return await self.gemini.generate_response(prompt)
            raise e

    def generate_with_history(self, messages, system_instruction=None, **kwargs):
        """
        Gera resposta com histórico, delegando para o adapter ativo.
        """
        # Determine active adapter
        adapter = self.gemini if self.primary == "google" else self.groq
        
        if adapter is None:
             adapter = self.groq # Fallback default
             
        if not adapter:
             raise Exception("Nenhum adaptador LLM disponível em SmartLLM")
             
        prepared_messages = self._prepare_messages_for_primary(messages)

        # Tentar chamar o método no adapter
        if hasattr(adapter, "generate_with_history"):
            return adapter.generate_with_history(prepared_messages, system_instruction, **kwargs)
        
        # Fallback se o adapter não tiver o método (ex: Groq antigo)
        # Tenta usar get_completion ignorando system_instruction dinâmico se necessário
        # Mas ideal é que todos adapters tenham a interface consistente.
        logger.warning(f"Adapter {type(adapter).__name__} não tem generate_with_history. Usando get_completion.")
        result = adapter.get_completion(prepared_messages)
        if "error" in result:
             raise Exception(result["error"])
        return result.get("content", "")

    def get_completion(self, messages: List[Dict[str, str]], tools: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Sync completion with automatic fallback on rate limit.
        Suporta fallback bidirecional (Groq -> Gemini OU Gemini -> Groq).
        """
        # 1. Identificar Primário e Secundário
        if self.primary == "google":
            primary_adapter = self.gemini
            secondary_adapter = self.groq
            secondary_name = "Groq"
        else:
            primary_adapter = self.groq
            secondary_adapter = self.gemini
            secondary_name = "Gemini"
        
        # Se primário (Gemini) não estiver disponível, degradar para Secundário imediatamente
        if primary_adapter is None:
            logger.info(f"Adapter primário ({self.primary}) indisponível. Usando {secondary_name} como fallback imediato.")
            primary_adapter = secondary_adapter
            secondary_adapter = None # Não há terceira opção
        
        # Propagar instruções de sistema
        if self.system_instruction:
            primary_adapter.system_instruction = self.system_instruction
            if secondary_adapter:
                secondary_adapter.system_instruction = self.system_instruction
        
        # 2. Tentar Primário
        primary_messages = self._prepare_messages_for_primary(messages)
        result = primary_adapter.get_completion(primary_messages, tools)
        
        # 3. Verificar Falha e Tentar Secundário
        if "error" in result and secondary_adapter:
            error_str = str(result.get("error", ""))
            
            # Decisão de Fallback: Rate Limit OU Erro de API 5xx do Google
            # Google as vezes retorna 500/503 em vez de 429
            should_fallback = self._is_rate_limit_error(error_str) or ("50" in error_str and self.primary == "google")
            
            if should_fallback:
                logger.warning(f"[RETRY] Erro no primário ({self.primary}): {error_str}. Tentando fallback para {secondary_name}...")

                compact_messages = self._compact_messages_for_fallback(messages)
                fallback_result = secondary_adapter.get_completion(compact_messages, tools)
                
                if "error" not in fallback_result:
                    logger.info(f"[OK] Fallback para {secondary_name} funcionou!")
                    return fallback_result
                else:
                    logger.warning(f"[ERROR] Fallback também falhou: {fallback_result.get('error')}")
                    return {"error": self._sanitize_user_error(str(fallback_result.get("error", "")))}
        
        if "error" in result:
            return {"error": self._sanitize_user_error(str(result.get("error", "")))}

        return result
