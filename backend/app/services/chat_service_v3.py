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
from typing import Dict, Any, Optional, Callable, Awaitable, Union
from dataclasses import dataclass

# Componentes do agente
from backend.app.core.agents.caculinha_bi_agent import CaculinhaBIAgent
from backend.app.core.agents.code_gen_agent import CodeGenAgent

# Componentes existentes
from backend.app.core.llm_factory import LLMFactory
from backend.app.core.utils.session_manager import SessionManager
from backend.app.core.utils.field_mapper import FieldMapper

logger = logging.getLogger(__name__)


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
        self.code_gen_agent = CodeGenAgent()
        
        # [OK] NOVO: Usar CaculinhaBIAgent em vez de componentes separados
        logger.info("[DEBUG] [DEBUG] Criando CaculinhaBIAgent...")
        self.agent = CaculinhaBIAgent(
            llm=self.llm,
            code_gen_agent=self.code_gen_agent,
            field_mapper=self.field_mapper,
            user_role="analyst",
            enable_rag=True
        )
        logger.info(f"[DEBUG] [DEBUG] CaculinhaBIAgent criado com sucesso: {type(self.agent)}")
        
        logger.info("[OK] ChatServiceV3 inicializado com CaculinhaBIAgent")
    
    async def process_message(
        self,
        query: str,
        session_id: str,
        user_id: str,
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
        
        try:
            # Callback helper
            # Callback helper
            async def emit_progress(arg1: Union[str, Dict[str, Any]], arg2: Optional[str] = None):
                if on_progress:
                    if isinstance(arg1, dict):
                        # Chamada do Agente (já é o evento completo)
                        await on_progress(arg1)
                    else:
                        # Chamada interna (tool, status)
                        await on_progress({
                            "type": "tool_progress",
                            "tool": arg1,
                            "status": arg2
                        })
            
            logger.info(f"[DEBUG] [DEBUG] Agente disponível: {self.agent is not None}")
            
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
            agent_response = await self.agent.run_async(
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
            
            # 5. Salvar no histórico
            self.session_manager.add_message(session_id, "user", query, user_id)
            response_text = response.get("result", {}).get("mensagem", "")
            self.session_manager.add_message(
                session_id, 
                "assistant", 
                response_text, 
                user_id
            )
            
            logger.info(f"[AGENT] Resposta gerada com sucesso")
            return response
            
        except Exception as e:
            logger.error(f"Erro em process_message: {e}", exc_info=True)
            return {
                "type": "text",
                "result": {"mensagem": f"Erro ao processar: {str(e)}"}
            }
    
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
