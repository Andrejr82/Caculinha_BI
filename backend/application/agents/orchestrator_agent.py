"""
OrchestratorAgent — Agente Orquestrador Principal

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse

logger = structlog.get_logger(__name__)


@dataclass
class PipelineContext:
    """Contexto compartilhado entre agentes no pipeline."""
    request: AgentRequest
    memory_context: Optional[Dict[str, Any]] = None
    rag_context: Optional[str] = None
    compressed_context: Optional[str] = None
    sql_results: Optional[List[Dict]] = None
    final_response: Optional[str] = None


class OrchestratorAgent(BaseAgent):
    """Agente principal que orquestra o pipeline cognitivo."""
    
    def __init__(
        self,
        memory_agent=None,
        vectorization_agent=None,
        rag_agent=None,
        ranking_agent=None,
        compression_agent=None,
        sql_agent=None,
        insight_agent=None,
        llm_client=None,
    ):
        super().__init__(
            name="OrchestratorAgent",
            description="Orquestra o pipeline cognitivo completo",
            capabilities=["orchestrate", "route", "coordinate"]
        )
        self.memory = memory_agent
        self.vectorization = vectorization_agent
        self.rag = rag_agent
        self.ranking = ranking_agent
        self.compression = compression_agent
        self.sql = sql_agent
        self.insight = insight_agent
        self.llm = llm_client
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        """Executa o pipeline cognitivo completo."""
        ctx = PipelineContext(request=request)
        
        try:
            # 1. Compressão (se necessário)
            ctx = await self._step_compression(ctx)
            
            # 2. Carregar memória
            ctx = await self._step_load_memory(ctx)
            
            # 3. Busca RAG
            ctx = await self._step_rag(ctx)
            
            # 4. Gerar resposta
            ctx = await self._step_generate(ctx)
            
            # 5. Salvar memória
            await self._step_save_memory(ctx)
            
            return AgentResponse(
                content=ctx.final_response or "Processamento concluído",
                agent_name=self.name,
                success=True,
                metadata={"pipeline_steps": 5}
            )
        except Exception as e:
            logger.error("orchestration_failed", error=str(e))
            return AgentResponse(content="", agent_name=self.name, success=False, error=str(e))
    
    async def _step_compression(self, ctx: PipelineContext) -> PipelineContext:
        """Step 1: Compressão de contexto."""
        if not self.compression or not self.memory:
            return ctx
        
        messages = await self.memory.load_memory(ctx.request.conversation_id, limit=20)
        if await self.compression.should_compress(messages):
            compressed = await self.compression.compress(messages)
            ctx.compressed_context = compressed.summary
            logger.info("context_compressed", ratio=compressed.compression_ratio)
        
        return ctx
    
    async def _step_load_memory(self, ctx: PipelineContext) -> PipelineContext:
        """Step 2: Carregar memória."""
        if not self.memory:
            return ctx
        
        messages = await self.memory.load_memory(ctx.request.conversation_id, limit=10)
        ctx.memory_context = {"messages": [m.to_dict() for m in messages]}
        return ctx
    
    async def _step_rag(self, ctx: PipelineContext) -> PipelineContext:
        """Step 3: Busca RAG."""
        if not self.rag:
            return ctx
        
        results = await self.rag.search(
            ctx.request.content,
            tenant_id=ctx.request.tenant_id,
            limit=5
        )
        ctx.rag_context = self.rag._format_context(results)
        return ctx
    
    async def _step_generate(self, ctx: PipelineContext) -> PipelineContext:
        """Step 4: Gerar resposta final."""
        if self.insight:
            ctx.final_response = await self.insight.generate_insight(
                ctx.request.content,
                {"rag_context": ctx.rag_context, "memory": ctx.memory_context}
            )
        elif self.llm:
            prompt = self._build_prompt(ctx)
            ctx.final_response = await self.llm.generate(prompt)
        else:
            ctx.final_response = f"Processado: {ctx.request.content}"
        
        return ctx
    
    async def _step_save_memory(self, ctx: PipelineContext) -> None:
        """Step 5: Salvar em memória."""
        if not self.memory:
            return
        
        from backend.domain.entities.message import Message
        
        # Salva mensagem do usuário
        user_msg = Message.user(ctx.request.conversation_id, ctx.request.content)
        await self.memory.save_message(user_msg)
        
        # Salva resposta do assistente
        if ctx.final_response:
            assistant_msg = Message.assistant(ctx.request.conversation_id, ctx.final_response)
            await self.memory.save_message(assistant_msg)
    
    def _build_prompt(self, ctx: PipelineContext) -> str:
        """Constrói prompt final com contexto."""
        parts = []
        
        if ctx.compressed_context:
            parts.append(f"### Histórico Resumido:\n{ctx.compressed_context}")
        
        if ctx.rag_context:
            parts.append(ctx.rag_context)
        
        parts.append(f"### Pergunta:\n{ctx.request.content}")
        
        return "\n\n".join(parts)
