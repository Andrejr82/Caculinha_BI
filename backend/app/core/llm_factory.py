import logging
from typing import Optional, List, Dict, Any
from app.config.settings import settings
from app.core.llm_groq_adapter import GroqLLMAdapter

logger = logging.getLogger(__name__)


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
        
        # FIX DEFINITIVO 2026-01-09: Verificar se Gemini está disponível no startup
        # Só marca como disponível se API key existir e parecer válida
        gemini_key = getattr(settings, 'GEMINI_API_KEY', None) or ""
        self._gemini_available = bool(gemini_key and len(gemini_key) > 10 and "expired" not in gemini_key.lower())
        
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
                from app.core.llm_genai_adapter import GenAILLMAdapter
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
             
        # Tentar chamar o método no adapter
        if hasattr(adapter, "generate_with_history"):
            return adapter.generate_with_history(messages, system_instruction, **kwargs)
        
        # Fallback se o adapter não tiver o método (ex: Groq antigo)
        # Tenta usar get_completion ignorando system_instruction dinâmico se necessário
        # Mas ideal é que todos adapters tenham a interface consistente.
        logger.warning(f"Adapter {type(adapter).__name__} não tem generate_with_history. Usando get_completion.")
        result = adapter.get_completion(messages)
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
        result = primary_adapter.get_completion(messages, tools)
        
        # 3. Verificar Falha e Tentar Secundário
        if "error" in result and secondary_adapter:
            error_str = str(result.get("error", ""))
            
            # Decisão de Fallback: Rate Limit OU Erro de API 5xx do Google
            # Google as vezes retorna 500/503 em vez de 429
            should_fallback = self._is_rate_limit_error(error_str) or ("50" in error_str and self.primary == "google")
            
            if should_fallback:
                logger.warning(f"[RETRY] Erro no primário ({self.primary}): {error_str}. Tentando fallback para {secondary_name}...")
                
                fallback_result = secondary_adapter.get_completion(messages, tools)
                
                if "error" not in fallback_result:
                    logger.info(f"[OK] Fallback para {secondary_name} funcionou!")
                    return fallback_result
                else:
                    logger.warning(f"[ERROR] Fallback também falhou: {fallback_result.get('error')}")
        
        return result