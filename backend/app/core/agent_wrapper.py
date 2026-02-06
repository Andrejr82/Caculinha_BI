"""
Wrapper simplificado para integração do sistema de agentes com FastAPI
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentWrapper:
    """
    Wrapper para integrar o sistema de agentes do Agent_Business com FastAPI
    """
    
    def __init__(self):
        self.query_processor = None
        self._initialize()
    
    def _initialize(self):
        """Inicializa o sistema de agentes"""
        try:
            # Configurar GEMINI_API_KEY se não estiver configurada
            if not os.getenv("GEMINI_API_KEY"):
                logger.warning("GEMINI_API_KEY não configurada, usando fallback")
                return
            
            # Importar QueryProcessor
            from app.core.query_processor import QueryProcessor
            
            self.query_processor = QueryProcessor()
            logger.info("Sistema de agentes inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema de agentes: {e}")
            self.query_processor = None
    
    def process_query(self, query: str) -> dict:
        """
        Processa uma consulta usando o sistema de agentes
        
        Args:
            query: Pergunta do usuário
            
        Returns:
            dict com type e output
        """
        if self.query_processor is None:
            return {
                "type": "text",
                "output": "Sistema de agentes não disponível. Verifique a configuração do GEMINI_API_KEY."
            }
        
        try:
            result = self.query_processor.process_query(query)
            return result
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {e}")
            return {
                "type": "text",
                "output": f"Erro ao processar consulta: {str(e)}"
            }


# Instância global do wrapper
_agent_wrapper = None


def get_agent_wrapper() -> AgentWrapper:
    """Retorna instância singleton do AgentWrapper"""
    global _agent_wrapper
    if _agent_wrapper is None:
        _agent_wrapper = AgentWrapper()
    return _agent_wrapper
