"""
ProcessChatUseCase — Caso de Uso de Chat

Implementa a lógica de processamento de mensagens de chat
seguindo Clean Architecture.

Uso:
    from backend.application.use_cases import ProcessChatUseCase
    
    use_case = ProcessChatUseCase(orchestrator, data_source)
    response = await use_case.execute(request)

Autor: Arquiteto de Sistema
Data: 2026-02-07
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import structlog

from backend.domain.ports.agent_port import AgentPort
from backend.domain.ports.data_source_port import DataSourcePort


logger = structlog.get_logger(__name__)


# =============================================================================
# REQUEST / RESPONSE DTOs
# =============================================================================

@dataclass
class ChatRequest:
    """Request DTO para processamento de chat."""
    message: str
    tenant_id: str
    user_id: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """Response DTO do processamento de chat."""
    response: str
    conversation_id: str
    agent_used: str
    tokens_used: int
    processing_time_ms: float
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# USE CASE
# =============================================================================

class ProcessChatUseCase:
    """
    Caso de uso principal para processamento de chat.
    
    Responsabilidades:
    - Validar input
    - Resolver contexto do tenant
    - Delegar para OrchestratorAgent
    - Formatar resposta
    - Registrar métricas
    """
    
    def __init__(
        self,
        orchestrator: AgentPort,
        data_source: Optional[DataSourcePort] = None,
    ):
        """
        Inicializa o use case.
        
        Args:
            orchestrator: Agente orquestrador
            data_source: Fonte de dados (opcional)
        """
        self.orchestrator = orchestrator
        self.data_source = data_source
    
    async def execute(self, request: ChatRequest) -> ChatResponse:
        """
        Executa o processamento de chat.
        
        Args:
            request: Request DTO com mensagem e contexto
        
        Returns:
            Response DTO com resposta e metadados
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "process_chat_started",
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            message_length=len(request.message),
        )
        
        try:
            # 1. Validar input
            self._validate_request(request)
            
            # 2. Preparar contexto
            context = self._prepare_context(request)
            
            # 3. Executar agente
            agent_response = await self.orchestrator.execute(
                task=request.message,
                context=context,
            )
            
            # 4. Calcular tempo
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # 5. Construir resposta
            response = ChatResponse(
                response=agent_response.get("response", ""),
                conversation_id=request.conversation_id or self._generate_conversation_id(),
                agent_used=agent_response.get("agent_used", "orchestrator"),
                tokens_used=agent_response.get("tokens_used", 0),
                processing_time_ms=processing_time,
                metadata=agent_response.get("metadata"),
            )
            
            logger.info(
                "process_chat_completed",
                tenant_id=request.tenant_id,
                agent_used=response.agent_used,
                processing_time_ms=response.processing_time_ms,
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "process_chat_failed",
                tenant_id=request.tenant_id,
                error=str(e),
            )
            raise
    
    def _validate_request(self, request: ChatRequest) -> None:
        """Valida o request."""
        if not request.message or not request.message.strip():
            raise ValueError("Message cannot be empty")
        
        if len(request.message) > 10000:
            raise ValueError("Message too long (max 10000 chars)")
        
        if not request.tenant_id:
            raise ValueError("Tenant ID is required")
        
        if not request.user_id:
            raise ValueError("User ID is required")
    
    def _prepare_context(self, request: ChatRequest) -> Dict[str, Any]:
        """Prepara contexto para o agente."""
        context = {
            "tenant_id": request.tenant_id,
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if request.context:
            context.update(request.context)
        
        return context
    
    def _generate_conversation_id(self) -> str:
        """Gera ID de conversa."""
        import uuid
        return f"conv-{uuid.uuid4().hex[:12]}"
