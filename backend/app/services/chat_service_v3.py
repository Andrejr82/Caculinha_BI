"""
Chat Service V3 - Arquitetura Agent-Based (Refatorado 2026-01-24)

Arquitetura Agent-Based - Usando CaculinhaBIAgent
Serviço principal que orquestra o fluxo agent-based com ferramentas.

Fluxo:
1. Obter histórico da sessão
2. Preparar contexto do usuário (RLS, filtros)
3. Executar CaculinhaBIAgent.run_async()
4. Processar resposta do agente
5. Salvar no histórico

Princípios:
- LLM decide quais ferramentas usar
- Agente tem acesso a 20+ ferramentas
- Resposta natural e contextualizada
- Compatibilidade com API existente
"""

import logging
import asyncio
import sys
import time
from typing import Dict, Any, Optional, Callable, Awaitable, Union
from dataclasses import dataclass

# Componentes do agente
from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.agents.code_gen_agent import CodeGenAgent

# Componentes existentes
from backend.app.core.llm_factory import LLMFactory
from backend.app.core.utils.session_manager import SessionManager
from backend.app.core.utils.field_mapper import FieldMapper
from backend.app.config.settings import settings
from backend.services.metrics import MetricsService

logger = logging.getLogger(__name__)

# Legacy namespace compatibility for contract/pipeline tests.
sys.modules.setdefault("app.services.chat_service_v3", sys.modules[__name__])


@dataclass
class SystemResponse:
    """
    Resposta do sistema (não gerada pela LLM).
    
    Usado para:
    - Erros
    - Esclarecimentos
    - Mensagens do sistema
    """
    message: str
    type: str  # "no_data", "error", "clarification_needed", "system"
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para resposta API"""
        result = {
            "type": "text",
            "result": {
                "mensagem": self.message
            },
            "system_response": True,
            "response_type": self.type
        }
        
        if self.suggestion:
            result["result"]["sugestao"] = self.suggestion
        
        return result


class ChatServiceV3:
    """
    Serviço de chat com arquitetura Agent-Based.
    
    Mudanças da refatoração (2026-01-24):
    - Usa CaculinhaBIAgent em vez de metrics-first
    - LLM decide quais ferramentas usar
    - Acesso a 20+ ferramentas de BI
    - Resposta mais flexível e contextualizada
    """
    
    def __init__(
        self,
        session_manager: SessionManager,
        parquet_path: Optional[str] = None
    ):
        """
        Args:
            session_manager: Gerenciador de sessões
            parquet_path: Caminho para o parquet (opcional)
        """
        self.session_manager = session_manager
        
        # Inicializar componentes
        logger.info("[DEBUG] [DEBUG] ChatServiceV3.__init__ INICIANDO (Agent-Based)...")
        
        # LLM adapter
        logger.info("[DEBUG] [DEBUG] Criando LLM adapter...")
        self.llm = LLMFactory.get_adapter(use_smart=True)
        logger.info(f"[DEBUG] [DEBUG] LLM adapter criado: {type(self.llm)}")
        
        # Field mapper para o agente
        logger.info("[DEBUG] [DEBUG] Criando FieldMapper...")
        self.field_mapper = FieldMapper()
        
        # CodeGenAgent (usado pelo CaculinhaBIAgent para cálculos complexos)
        logger.info("[DEBUG] [DEBUG] Criando CodeGenAgent...")
        try:
            self.code_gen_agent = CodeGenAgent()
        except Exception as e:
            logger.warning(f"CodeGenAgent indisponível no ambiente atual: {e}")
            self.code_gen_agent = None
        
        # [OK] NOVO: Usar CaculinhaBIAgent em vez de componentes separados
        logger.info("[DEBUG] [DEBUG] Criando CaculinhaBIAgent (default=analyst)...")
        self.agent = CaculinhaBIAgent(
            llm=self.llm,
            code_gen_agent=self.code_gen_agent,
            field_mapper=self.field_mapper,
            user_role="analyst",
            enable_rag=True
        )
        # Cache de agentes por role para evitar recriação por request
        self._agents_by_role: Dict[str, CaculinhaBIAgent] = {"analyst": self.agent}
        logger.info(f"[DEBUG] [DEBUG] CaculinhaBIAgent criado com sucesso: {type(self.agent)}")
        
        logger.info("[OK] ChatServiceV3 inicializado com CaculinhaBIAgent")

    def get_llm_status(self) -> Dict[str, Any]:
        """
        Retorna status dos provedores LLM em uso.
        """
        if hasattr(self.llm, "get_provider_status"):
            return self.llm.get_provider_status()
        raw_provider = (getattr(settings, "LLM_PROVIDER", "") or "").strip().lower()
        provider_aliases = {"grq": "groq", "gemini": "google"}
        provider = provider_aliases.get(raw_provider, raw_provider or "unknown")
        model_name = getattr(settings, "GROQ_MODEL_NAME", None) if provider == "groq" else getattr(settings, "LLM_MODEL_NAME", None)
        return {
            "primary": provider,
            "chain": [provider],
            "providers": [
                {
                    "provider": provider,
                    "available": True,
                    "model": model_name,
                    "capabilities": {"chat": True, "tools": False, "streaming": False, "json_mode": False},
                }
            ],
        }

    @staticmethod
    def _estimate_tokens(text: Optional[str]) -> int:
        """
        Estimativa simples de tokens para observabilidade operacional.
        Aproximação: ~4 chars por token.
        """
        if not text:
            return 0
        return max(1, int(len(str(text)) / 4))

    @staticmethod
    def _extract_tool_call_names(tool_calls: Any) -> list[str]:
        names: list[str] = []
        if not tool_calls:
            return names
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                if isinstance(tc, str):
                    names.append(tc)
                    continue
                if isinstance(tc, dict):
                    function_obj = tc.get("function")
                    if isinstance(function_obj, dict) and function_obj.get("name"):
                        names.append(str(function_obj["name"]))
                        continue
                    if tc.get("name"):
                        names.append(str(tc["name"]))
        return names

    @staticmethod
    def _classify_query_complexity(query: str) -> str:
        q = (query or "").lower()
        complex_markers = (
            "grafico", "gráfico", "dashboard", "forecast", "previs",
            "anomalia", "outlier", "alocar", "transfer", "otimiz",
            "segmento", "categoria", "correlação", "correlacao",
        )
        if len(q) > 120 or any(marker in q for marker in complex_markers):
            return "complex"
        return "simple"
    
    async def process_message(
        self,
        query: str,
        session_id: str,
        user_id: str,
        user_role: str = "analyst",
        on_progress: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Processa uma mensagem usando CaculinhaBIAgent.
        
        Args:
            query: Query do usuário
            session_id: ID da sessão
            user_id: ID do usuário
            on_progress: Callback para eventos de progresso
        
        Returns:
            Dicionário com resposta (compatível com API existente)
        """
        logger.info(f"[DEBUG] [DEBUG] process_message INICIANDO: query='{query[:100]}...'")

        request_started_at = time.perf_counter()
        metrics = MetricsService()
        normalized_role_for_metrics = self._normalize_role(user_role)
        complexity = self._classify_query_complexity(query)

        metrics.increment("chat_requests_total")
        metrics.increment("chat_requests_total", labels={"role": normalized_role_for_metrics})

        try:
            # Callback helper
            # Callback helper
            async def emit_progress(arg1: Union[str, Dict[str, Any]], arg2: Optional[str] = None):
                if on_progress:
                    if isinstance(arg1, dict):
                        # Chamada do Agente (já é o evento completo)
                        await on_progress(arg1)
                    else:
                        tool_map = {
                            "Analisando pergunta": "system.thinking",
                            "Pensando": "system.thinking",
                            "Processando resposta": "system.finalizing",
                            "consultar_dados_flexivel": "tool.data_query",
                            "consultar_dados_gerais": "tool.metadata_query",
                            "gerar_grafico_universal": "tool.chart",
                            "gerar_grafico_universal_v2": "tool.chart",
                            "pesquisar_precos_concorrentes": "tool.competitive_research",
                            "pesquisar_mercado_web": "tool.market_research",
                        }
                        status_map = {
                            "start": "start",
                            "executing": "executing",
                            "processing": "finishing",
                            "done": "finishing",
                            "finishing": "finishing",
                        }
                        # Chamada interna (tool, status)
                        await on_progress({
                            "type": "tool_progress",
                            "tool": tool_map.get(str(arg1), f"tool.{str(arg1 or 'generic')}"),
                            "status": status_map.get(str(arg2 or "").lower(), "executing")
                        })
            
            role = normalized_role_for_metrics
            agent = self._get_agent_for_role(role)
            logger.info(f"[DEBUG] [DEBUG] Agente disponível para role '{role}': {agent is not None}")
            
            # 1. Obter histórico
            chat_history = self.session_manager.get_history(session_id, user_id)
            
            # 2. Preparar contexto do usuário (RLS, etc)
            user_filters = self._get_user_filters(user_id)
            user_context = {
                "user_id": user_id,
                "session_id": session_id,
                "filters": user_filters
            }
            
            # 3. Executar agente
            await emit_progress("Analisando pergunta", "start")
            
            # Converter histórico para formato esperado pelo agente
            agent_history = self._convert_history_format(chat_history)
            logger.info(f"[DEBUG] [DEBUG] Histórico convertido: {len(agent_history)} mensagens")
            
            # Executar agente de forma assíncrona
            # Executar agente de forma assíncrona
            logger.info(f"[DEBUG] [DEBUG] Chamando agent.run_async()...")
            
            # FIX: run_async é nativamente async, não usar threads para ele
            agent_response = await agent.run_async(
                query,
                agent_history, # Pass converted history directly
                on_progress=emit_progress # Pass progress callback if supported
            )
            logger.info(f"[DEBUG] [DEBUG] agent.run_async() RETORNOU: {type(agent_response)}")
            logger.info(f"[DEBUG] [DEBUG] Resposta do agente: {str(agent_response)[:200]}...")
            
            # TRAP: Se for coroutine, logar erro critico
            if asyncio.iscoroutine(agent_response):
                logger.error("[ERROR] CRITICAL: agent_response IS A COROUTINE! Force awaiting it...")
                agent_response = await agent_response
                logger.info("[OK] Recovered from coroutine state.")
            
            await emit_progress("Analisando pergunta", "done")
            
            # 4. Processar resposta do agente
            response = self._process_agent_response(agent_response)

            # Métricas de tool usage/tokens/custo aproximado
            tool_names = self._extract_tool_call_names(agent_response.get("tool_calls") if isinstance(agent_response, dict) else None)
            if tool_names:
                metrics.increment("chat_tool_calls_total", value=len(tool_names))
                for tool_name in tool_names:
                    metrics.increment("chat_tool_calls_total", labels={"tool": tool_name})

            # 5. Salvar no histórico
            self.session_manager.add_message(session_id, "user", query, user_id)
            response_text = response.get("result", {}).get("mensagem", "")
            self.session_manager.add_message(
                session_id, 
                "assistant", 
                response_text, 
                user_id
            )

            tokens_in = self._estimate_tokens(query)
            tokens_out = self._estimate_tokens(response_text)
            metrics.increment("chat_tokens_in_total", value=tokens_in)
            metrics.increment("chat_tokens_out_total", value=tokens_out)
            metrics.increment("chat_tokens_total", value=tokens_in + tokens_out)

            latency_seconds = max(0.0, time.perf_counter() - request_started_at)
            metrics.observe("chat_latency_seconds", latency_seconds)
            metrics.observe("chat_latency_seconds", latency_seconds, labels={"complexity": complexity})
            metrics.observe("agent_execution_seconds", latency_seconds)
            
            logger.info(f"[AGENT] Resposta gerada com sucesso")
            return response
            
        except Exception as e:
            metrics.increment("chat_errors_total")
            metrics.increment("chat_errors_total", labels={"role": normalized_role_for_metrics})
            latency_seconds = max(0.0, time.perf_counter() - request_started_at)
            metrics.observe("chat_latency_seconds", latency_seconds)
            metrics.observe("chat_latency_seconds", latency_seconds, labels={"complexity": complexity})
            logger.error(f"Erro em process_message: {e}", exc_info=True)
            return {
                "type": "text",
                "result": {"mensagem": f"Erro ao processar: {str(e)}"}
            }

    def _get_agent_for_role(self, role: str) -> CaculinhaBIAgent:
        """Retorna (ou cria) um agente com escopo de ferramentas por role."""
        if role in self._agents_by_role:
            return self._agents_by_role[role]

        logger.info(f"[DEBUG] Criando agente para role dinâmica: {role}")
        scoped_agent = CaculinhaBIAgent(
            llm=self.llm,
            code_gen_agent=self.code_gen_agent,
            field_mapper=self.field_mapper,
            user_role=role,
            enable_rag=True
        )
        self._agents_by_role[role] = scoped_agent
        return scoped_agent

    def _normalize_role(self, user_role: Optional[str]) -> str:
        """
        Normaliza papel do usuário para escopo de ferramentas do agente.
        Mantém experiência funcional do chat para perfis de negócio.
        """
        role = (user_role or "analyst").strip().lower()
        role_map = {
            "admin": "admin",
            "analyst": "analyst",
            "user": "analyst",
            "compras": "analyst",
            "coordenador": "analyst",
            "coordinator": "analyst",
            "gerente": "analyst",
            "manager": "analyst",
            "viewer": "viewer",
            "guest": "guest",
        }
        normalized = role_map.get(role, "analyst")
        if normalized != role:
            logger.info(f"[DEBUG] Role normalizada para escopo do chat: '{role}' -> '{normalized}'")
        return normalized
    
    def _convert_history_format(self, chat_history: list) -> list:
        """
        Converte histórico do SessionManager para formato esperado pelo agente.
        
        SessionManager format: [{"role": "user/assistant", "content": str, ...}]
        Agent format: [{"role": "user/assistant", "content": str}]
        """
        converted = []
        for msg in chat_history:
            converted.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        return converted
    
    def _process_agent_response(self, agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte resposta do agente para formato esperado pela API.
        
        Agent response format:
        {
            "response": str,
            "tool_calls": [...],
            "chart_data": {...} (opcional)
        }
        
        API expected format:
        {
            "type": "text",
            "result": {"mensagem": str},
            "chart_data": {...} (opcional)
        }
        """
        logger.info(f"[DEBUG] [DEBUG] _process_agent_response INPUT: {str(agent_response)[:500]}...")
        
        # FIX 2026-01-27: Extração robusta de response_text com múltiplos fallbacks
        response_text = None
        
        # Tentativa 1: Chave "response" (formato padrão do agente)
        if "response" in agent_response and agent_response["response"]:
            response_text = agent_response["response"]
            logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'response': {response_text[:100]}...")
        
        # Tentativa 2: Chave "text_override"
        elif "text_override" in agent_response and agent_response["text_override"]:
            response_text = agent_response["text_override"]
            logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'text_override': {response_text[:100]}...")
        
        # Tentativa 3: Chave "result" (se for string)
        elif "result" in agent_response:
            result_data = agent_response["result"]
            if isinstance(result_data, str) and result_data:
                response_text = result_data
                logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'result' (string): {response_text[:100]}...")
            elif isinstance(result_data, dict) and "mensagem" in result_data:
                response_text = result_data["mensagem"]
                logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'result.mensagem': {response_text[:100]}...")
        
        # Tentativa 4: Chave "mensagem" direta
        elif "mensagem" in agent_response and agent_response["mensagem"]:
            response_text = agent_response["mensagem"]
            logger.info(f"[DEBUG] [DEBUG] response_text extraído de 'mensagem': {response_text[:100]}...")
        
        # Fallback final: Se ainda vazio, usar mensagem padrão
        if not response_text or (isinstance(response_text, str) and not response_text.strip()):
            logger.warning(f"[WARNING] [DEBUG] response_text VAZIO! agent_response keys: {agent_response.keys()}")
            response_text = "Desculpe, não consegui gerar uma resposta adequada. Por favor, reformule sua pergunta."
            
        # Handle chart data keys
        chart_data = agent_response.get("chart_data")
        if not chart_data:
            chart_data = agent_response.get("chart_spec")
        
        if chart_data:
            logger.info(f"[DEBUG] [DEBUG] chart_data encontrado: {str(chart_data)[:200]}...")
        
        result = {
            "type": "text",
            "result": {
                "mensagem": response_text
            }
        }
        
        # Adicionar chart_data se existir
        if chart_data:
            result["chart_data"] = chart_data
        
        logger.info(f"[DEBUG] [DEBUG] _process_agent_response OUTPUT: {str(result)[:500]}...")
        return result
    
    def _get_user_filters(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém filtros do usuário para RLS (Row-Level Security).
        
        TODO: Implementar lógica real de RLS baseada em permissões do usuário.
        Por enquanto, retorna filtros vazios (sem restrição).
        """
        # Placeholder - implementar lógica real de RLS
        return {}
