"""
InsightAgent — Agente de Geração de Insights

Autor: Orchestrator Agent
Data: 2026-02-07
"""

from typing import Any, Dict, List, Optional
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse

logger = structlog.get_logger(__name__)


class InsightAgent(BaseAgent):
    """Agente responsável por gerar insights a partir de dados."""
    
    def __init__(self, llm_client=None, model: str = "gemini-2.5-flash-lite"):
        super().__init__(
            name="InsightAgent",
            description="Gera insights e narrativas a partir de dados",
            capabilities=["analyze", "summarize", "recommend"]
        )
        self.llm = llm_client
        self.model = model
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        insight = await self.generate_insight(request.content, request.context)
        return AgentResponse(content=insight, agent_name=self.name)
    
    async def generate_insight(self, query: str, data: Optional[Dict[str, Any]] = None) -> str:
        """Gera insight a partir de query e dados."""
        if not self.llm:
            return self._generate_basic_insight(query, data)
        
        prompt = self._build_insight_prompt(query, data)
        try:
            return await self.llm.generate(prompt, max_tokens=1000)
        except Exception as e:
            logger.error("insight_generation_failed", error=str(e))
            return self._generate_basic_insight(query, data)
    
    def _build_insight_prompt(self, query: str, data: Optional[Dict[str, Any]]) -> str:
        """Constrói prompt para geração de insight."""
        data_context = ""
        if data:
            data_context = f"\n\nDADOS DISPONÍVEIS:\n{self._format_data(data)}"
        
        return f"""Você é um analista de BI especializado em varejo.
Analise os dados e responda à pergunta do usuário de forma clara e acionável.
Use linguagem natural, evite jargões técnicos.
Inclua números e métricas relevantes.
{data_context}

PERGUNTA: {query}

ANÁLISE:"""
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """Formata dados para contexto."""
        parts = []
        for key, value in data.items():
            if isinstance(value, list) and value:
                parts.append(f"- {key}: {len(value)} registros")
                if len(value) <= 5:
                    parts.append(f"  Amostra: {value}")
            else:
                parts.append(f"- {key}: {value}")
        return "\n".join(parts)
    
    def _generate_basic_insight(self, query: str, data: Optional[Dict[str, Any]]) -> str:
        """Insight básico sem LLM."""
        if not data:
            return f"Para responder sobre '{query}', preciso de dados contextuais."
        
        metrics = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                metrics.append(f"{key}: {value:,.2f}")
            elif isinstance(value, list):
                metrics.append(f"{key}: {len(value)} itens")
        
        return f"Análise de '{query}':\n" + "\n".join(metrics) if metrics else "Dados insuficientes."
    
    async def analyze_trend(self, data: List[Dict], date_field: str, value_field: str) -> str:
        """Analisa tendência temporal."""
        if len(data) < 2:
            return "Dados insuficientes para análise de tendência."
        
        first_val = data[0].get(value_field, 0)
        last_val = data[-1].get(value_field, 0)
        
        if first_val == 0:
            return "Valor inicial zero, impossível calcular variação."
        
        variation = ((last_val - first_val) / first_val) * 100
        trend = "crescente" if variation > 0 else "decrescente" if variation < 0 else "estável"
        
        return f"Tendência {trend}: variação de {variation:.1f}% no período analisado."
