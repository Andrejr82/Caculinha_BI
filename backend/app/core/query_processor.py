# core/query_processor.py
import logging

try:
    from backend.app.core.agents.supervisor_agent import SupervisorAgent
except ImportError as e:
    logging.getLogger(__name__).warning(f"Failed to import SupervisorAgent: {e}")
    SupervisorAgent = None

from backend.app.core.factory.component_factory import ComponentFactory
from backend.app.core.llm_factory import LLMFactory
from backend.app.core.cache import Cache


class QueryProcessor:
    """
    Ponto de entrada principal para o processamento de consultas.
    Delega a tarefa para o SupervisorAgent para orquestração.
    """

    def __init__(self):
        """
        Inicializa o processador de consultas e o agente supervisor.
        """
        self.logger = logging.getLogger(__name__)
        
        # ⚡ OTIMIZAÇÃO: Inicializar sistema de resposta rápida (usando Polars diretamente)
        try:
            from backend.app.core.tools.quick_response import create_quick_response_system
            from backend.app.core.parquet_cache import cache

            # [OK] Usar Polars DataFrame diretamente (sem conversão para Pandas)
            df_polars = cache.get_dataframe("admmat.parquet")
            self.quick_response = create_quick_response_system(df_polars)
            self.logger.info("⚡ Quick Response System inicializado com Polars!")
        except Exception as e:
            self.logger.warning(f"Quick Response System não disponível: {e}")
            self.quick_response = None
        
        # Usar factory para obter adapter com fallback automático
        try:
            self.llm_adapter = LLMFactory.get_adapter()
            if SupervisorAgent:
                self.supervisor = SupervisorAgent(gemini_adapter=self.llm_adapter)
                self.logger.info(
                    "QueryProcessor inicializado e pronto para delegar ao SupervisorAgent."
                )
            else:
                self.supervisor = None
                self.logger.warning("SupervisorAgent não disponível (erro de importação).")
                
            self.cache = Cache()

        except ValueError as e:
            self.logger.error(f"Erro ao inicializar QueryProcessor: {e}")
            self.llm_adapter = None
            self.supervisor = None
            self.cache = Cache()
            raise RuntimeError(
                "GEMINI_API_KEY não configurada. Configure a chave da API do Google Gemini nos secrets do Streamlit Cloud."
            ) from e

    def process_query(self, query: str) -> dict:
        """
        Processa a consulta do usuário, delegando-a diretamente ao SupervisorAgent.

        Args:
            query (str): A consulta do usuário.

        Returns:
            dict: O resultado do processamento pelo agente especialista apropriado.
        """
        # [OK] FASE 1: QUICK RESPONSE BYPASS (< 500ms)
        # Responde queries simples SEM LLM (95% dos casos)
        if self.quick_response:
            quick_answer = self.quick_response.try_quick_response(query)
            if quick_answer:
                self.logger.info(f"⚡ Quick Response! Tempo: < 500ms | Query: {query[:50]}")
                return {"type": "text", "output": quick_answer}

        # Verificar se o supervisor foi inicializado
        if self.supervisor is None:
            return {
                "type": "text",
                "output": "[WARNING] **Sistema de Agentes Indisponível**\n\nO Agente Supervisor não pôde ser inicializado (possível erro de importação ou configuração). Apenas consultas simples (Quick Response) estão disponíveis."
            }

        # Interceptar perguntas sobre o nome do agente
        if query.lower() in ["qual seu nome", "quem é você", "qual o seu nome"]:
            return {
                "type": "text",
                "output": "Eu sou um Agente de Negócios, pronto para ajudar com suas análises de dados."
            }

        cached_result = self.cache.get(query)
        if cached_result:
            self.logger.info(
                f'Resultado recuperado do cache para a consulta: "{query}"'
            )
            return cached_result

        self.logger.info(f'Delegando a consulta para o Supervisor: "{query}"')
        result = self.supervisor.route_query(query)
        self.cache.set(query, result)
        return result

    def stream_query(self, query: str):
        """
        Processa a consulta do usuário com streaming de eventos do agente.

        Args:
            query (str): A consulta do usuário.

        Yields:
            dict: Eventos do agente (chunks de texto, ações, etc.)
        """
        # ⚡ OTIMIZAÇÃO: Tentar resposta rápida primeiro (< 500ms)
        if self.quick_response:
            quick_answer = self.quick_response.try_quick_response(query)
            if quick_answer:
                self.logger.info(f"⚡ Resposta rápida encontrada! Tempo: < 500ms")
                # Enviar resposta rápida em chunks para simular streaming
                for char in quick_answer:
                    yield {
                        "type": "text",
                        "content": char
                    }
                return

        # Verificar se o supervisor foi inicializado
        if self.supervisor is None:
            yield {
                "type": "text",
                "content": "[WARNING] **Sistema de Agentes Indisponível**\n\nO Agente Supervisor não pôde ser inicializado."
            }
            return

        # Interceptar perguntas simples (sem cache em streaming)
        if query.lower() in ["qual seu nome", "quem é você", "qual o seu nome"]:
            yield {
                "type": "text",
                "content": "Eu sou um Agente de Negócios, pronto para ajudar com suas análises de dados."
            }
            return

        self.logger.info(f'Streaming da consulta para o Supervisor: "{query}"')
        
        # Delegar para método de streaming do supervisor
        for event in self.supervisor.stream_query(query):
            yield event
