import logging
import sys
from typing import Optional, List, Dict, Any
from backend.app.config.settings import settings
from backend.app.core.llm_groq_adapter import GroqLLMAdapter
from backend.app.core.llm_base import BaseLLMAdapter

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
    
    _PROVIDER_ALIASES = {
        "google": "google",
        "gemini": "google",
        "groq": "groq",
        "mock": "mock",
    }

    class _MockLLMAdapter(BaseLLMAdapter):
        provider = "mock"
        model_name = "mock-llm"

        def get_capabilities(self) -> BaseLLMAdapter.Capabilities:
            return BaseLLMAdapter.Capabilities(chat=True, tools=False, streaming=False, json_mode=False)

        def get_completion(self, messages: List[Dict[str, Any]], tools: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            prompt = ""
            if messages:
                prompt = str(messages[-1].get("content", "")).strip()
            return {"content": f"[MOCK] Resposta simulada para: {prompt}"}

        async def generate_response(self, prompt: str) -> str:
            return f"[MOCK] Resposta simulada para: {prompt}"

    def __init__(self, primary: Optional[str] = None):
        self.primary = self._normalize_provider(primary or settings.LLM_PROVIDER or "google")
        self._groq = None  # Lazy init
        self._gemini = None  # Lazy init
        self._mock = None
        self.system_instruction = None  # Será setado pelo CaculinhaBIAgent
        self.dev_fast_mode = bool(getattr(settings, "DEV_FAST_MODE", False))

        gemini_key = getattr(settings, 'GEMINI_API_KEY', None) or ""
        self._gemini_available = bool(gemini_key and len(gemini_key) > 10 and "expired" not in gemini_key.lower())
        if self.dev_fast_mode and self.primary == "groq":
            self._gemini_available = False

        if not self._gemini_available:
            logger.info("SmartLLM: Gemini desabilitado (sem API key válida). Usando apenas Groq.")

        self.provider_chain = self._build_provider_chain(self.primary)
        logger.info(
            f"SmartLLM initialized: primary={self.primary}, chain={self.provider_chain}, "
            f"gemini_available={self._gemini_available}"
        )

    def _normalize_provider(self, provider: str) -> str:
        key = (provider or "").strip().lower()
        return self._PROVIDER_ALIASES.get(key, "groq")

    def _build_provider_chain(self, primary: str) -> List[str]:
        configured = [
            self._normalize_provider(item)
            for item in str(getattr(settings, "LLM_FALLBACK_PROVIDERS", "groq,google")).split(",")
            if item and str(item).strip()
        ]
        chain = [primary] + configured
        seen = set()
        unique_chain: List[str] = []
        for item in chain:
            if item not in seen:
                unique_chain.append(item)
                seen.add(item)
        return unique_chain


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

    @property
    def mock(self):
        if self._mock is None:
            self._mock = self._MockLLMAdapter()
        return self._mock

    def _get_adapter(self, provider: str):
        if provider == "groq":
            try:
                return self.groq
            except Exception as e:
                logger.warning(f"Groq indisponível: {e}")
                return None
        if provider == "google":
            return self.gemini
        if provider == "mock":
            return self.mock
        return None

    def get_provider_status(self) -> Dict[str, Any]:
        providers: List[Dict[str, Any]] = []
        for provider in self.provider_chain:
            adapter = self._get_adapter(provider)
            if adapter is None:
                providers.append(
                    {
                        "provider": provider,
                        "available": False,
                        "model": None,
                        "capabilities": None,
                    }
                )
                continue

            capabilities = {}
            try:
                caps = adapter.get_capabilities()
                capabilities = {
                    "chat": bool(getattr(caps, "chat", False)),
                    "tools": bool(getattr(caps, "tools", False)),
                    "streaming": bool(getattr(caps, "streaming", False)),
                    "json_mode": bool(getattr(caps, "json_mode", False)),
                }
            except Exception:
                capabilities = {"chat": True, "tools": False, "streaming": False, "json_mode": False}

            providers.append(
                {
                    "provider": provider,
                    "available": True,
                    "model": getattr(adapter, "model_name", None),
                    "capabilities": capabilities,
                }
            )

        return {"primary": self.primary, "chain": self.provider_chain, "providers": providers}

    def _is_rate_limit_error(self, error_str: str) -> bool:
        """Check if error indicates rate limiting"""
        error_lower = error_str.lower()
        return any(x in error_lower for x in ["429", "quota", "rate limit", "resource_exhausted"])

    def _is_payload_too_large_error(self, error_str: str) -> bool:
        error_lower = error_str.lower()
        return any(x in error_lower for x in ["413", "payload too large", "request too large", "tokens per minute"])

    def _sanitize_user_error(self, raw_error: str) -> str:
        err = (raw_error or "").lower()
        if "tool_use_failed" in err or "tool call validation failed" in err:
            return "Falha de validacao de parametros na chamada de ferramenta. Ajuste a pergunta ou tente novamente."
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
        """Async generation with provider-chain fallback."""
        last_error = "Nenhum provedor LLM disponível"
        for provider in self.provider_chain:
            adapter = self._get_adapter(provider)
            if adapter is None:
                continue
            try:
                if hasattr(adapter, "generate_response"):
                    return await adapter.generate_response(prompt)
                result = adapter.get_completion([{"role": "user", "content": prompt}], tools=None)
                if "error" not in result:
                    return str(result.get("content", ""))
                last_error = str(result.get("error", "erro desconhecido"))
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Falha em {provider} durante generate_response: {e}")
        raise Exception(self._sanitize_user_error(last_error))

    def generate_with_history(self, messages, system_instruction=None, **kwargs):
        """
        Gera resposta com histórico, delegando para o adapter ativo.
        """
        last_error = "Nenhum adaptador LLM disponível em SmartLLM"
        for idx, provider in enumerate(self.provider_chain):
            adapter = self._get_adapter(provider)
            if adapter is None:
                continue

            prepared_messages = self._prepare_messages_for_primary(messages) if idx == 0 else self._compact_messages_for_fallback(messages)
            try:
                if self.system_instruction and hasattr(adapter, "system_instruction"):
                    adapter.system_instruction = self.system_instruction

                if hasattr(adapter, "generate_with_history"):
                    return adapter.generate_with_history(prepared_messages, system_instruction, **kwargs)

                result = adapter.get_completion(prepared_messages)
                if "error" not in result:
                    return result.get("content", "")
                last_error = str(result.get("error", "erro desconhecido"))
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Falha em {provider} durante generate_with_history: {e}")

        raise Exception(self._sanitize_user_error(last_error))

    def get_completion(self, messages: List[Dict[str, str]], tools: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Sync completion with provider-chain fallback.
        """
        errors: List[str] = []

        for idx, provider in enumerate(self.provider_chain):
            adapter = self._get_adapter(provider)
            if adapter is None:
                errors.append(f"{provider}: indisponível")
                continue

            request_messages = self._prepare_messages_for_primary(messages) if idx == 0 else self._compact_messages_for_fallback(messages)

            try:
                if self.system_instruction and hasattr(adapter, "system_instruction"):
                    adapter.system_instruction = self.system_instruction

                result = adapter.get_completion(request_messages, tools)
                if not isinstance(result, dict):
                    errors.append(f"{provider}: resposta inválida")
                    continue

                if "error" in result:
                    errors.append(f"{provider}: {result.get('error')}")
                    logger.warning(f"[RETRY] {provider} falhou: {result.get('error')}")
                    continue

                result["provider"] = provider
                return result
            except Exception as e:
                errors.append(f"{provider}: {e}")
                logger.warning(f"[RETRY] {provider} exceção: {e}", exc_info=True)

        final_error = " | ".join(errors) if errors else "Nenhum provedor LLM disponível"
        return {"error": self._sanitize_user_error(final_error)}
