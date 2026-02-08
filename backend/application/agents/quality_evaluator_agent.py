"""
QualityEvaluatorAgent — Agente de Auditoria e Governança de Respostas

Este agente avalia a qualidade, utilidade e groundedness das respostas geradas
pelo InsightAgent antes de serem enviadas ao usuário final.

Autor: Antigravity AI
Data: 2026-02-07
"""

import json
import re
from typing import Any, Dict, List, Optional
import structlog

from backend.application.agents.base_agent import BaseAgent, AgentRequest, AgentResponse
from backend.app.core.llm_factory import LLMFactory

logger = structlog.get_logger(__name__)

class QualityEvaluatorAgent(BaseAgent):
    """
    Agente Auditor Senior de Varejo.
    Responsável por garantir que a IA não alucine e forneça valor real.
    """
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="QualityEvaluatorAgent",
            description="Audita respostas de IA para garantir groundedness e utilidade",
            capabilities=["audit", "score", "validate_rag"]
        )
        # Se não for passado um client, usa o factory (SmartLLM)
        self.llm = llm_client or LLMFactory.get_adapter(use_smart=True)
    
    async def _execute(self, request: AgentRequest) -> AgentResponse:
        """
        Executa a avaliação. 
        O request.content deve conter a resposta final a ser avaliada.
        O request.context deve conter 'user_query' e 'rag_context'.
        """
        user_query = request.context.get("user_query", "")
        agent_response = request.content
        rag_context = request.context.get("rag_context", "Nenhum dado RAG disponível.")
        
        evaluation = await self.evaluate_response(user_query, agent_response, rag_context)
        
        return AgentResponse(
            content=json.dumps(evaluation),
            agent_name=self.name,
            metadata=evaluation
        )

    async def evaluate_response(self, query: str, response: str, rag_context: Any) -> Dict[str, Any]:
        """
        Avalia a resposta usando LLM-as-a-Judge.
        """
        prompt = self._build_evaluation_prompt(query, response, rag_context)
        
        try:
            # Prepara mensagens para o adapter (que espera lista de dicts ou string no generate_response)
            if hasattr(self.llm, "generate_response"):
                raw_response = await self.llm.generate_response(prompt)
            else:
                # Fallback para get_completion
                msg = [{"role": "user", "content": prompt}]
                completion = self.llm.get_completion(msg)
                raw_response = completion.get("content", "{}")
            
            evaluation = self._parse_json_response(raw_response)
            
            # Validação básica de segurança se o JSON falhar
            if not evaluation or "scores" not in evaluation:
                evaluation = self._generate_fallback_evaluation("Erro ao processar JSON de avaliação.")
            
            return evaluation
            
        except Exception as e:
            logger.error("evaluation_failed", error=str(e))
            return self._generate_fallback_evaluation(str(e))

    def _build_evaluation_prompt(self, query: str, response: str, rag_context: Any) -> str:
        """Constrói o prompt de auditoria Context7."""
        return f"""Você é um Auditor de Dados de Varejo Senior (Senior Retail Data Auditor).
Sua missão é avaliar a resposta gerada por um Agente de IA para um usuário.

### CONTEXTO RAG (DADOS REAIS):
{rag_context}

### PERGUNTA DO USUÁRIO:
{query}

### RESPOSTA GERADA PELO AGENTE:
{response}

### INSTRUÇÕES DE AUDITORIA:
Avalie a resposta nos pilares abaixo (nota de 0.0 a 1.0):
1. **groundedness**: A resposta é fiel aos DADOS REAIS acima? Se a IA citar números ou colunas que não estão no contexto, a nota deve ser baixa.
2. **utility**: A resposta é útil para um gestor de loja? Contém ações claras ou análise de tendências?
3. **quality**: O texto é profissional, segue o formato narrativo e é fácil de entender?

### FORMATO DE SAÍDA OBRIGATÓRIO (JSON):
Retorne APENAS um JSON no formato abaixo, sem explicações extras:
{{
  "scores": {{
    "quality": 0.0,
    "utility": 0.0,
    "groundedness": 0.0
  }},
  "reasoning": {{
    "quality": "Justificativa...",
    "utility": "Justificativa...",
    "groundedness": "Justificativa..."
  }},
  "final_decision": "OK" | "WARNING" | "BLOCK"
}}

*Thresholds:*
- final_decision = "OK" se todos os scores >= 0.8
- final_decision = "WARNING" se algum score < 0.8 mas >= 0.5
- final_decision = "BLOCK" se algum score < 0.5

JSON:"""

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extrai e faz o parse do JSON na resposta do LLM."""
        try:
            # Tenta encontrar JSON no texto (casos onde o LLM coloca markdown boxes)
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return json.loads(text)
        except Exception:
            logger.warning("json_parse_failed", raw_text=text)
            return {}

    def _generate_fallback_evaluation(self, error: str) -> Dict[str, Any]:
        """Gera uma avaliação segura em caso de erro no agente."""
        return {
            "scores": {"quality": 0.5, "utility": 0.5, "groundedness": 0.5},
            "reasoning": {"error": f"Falha na avaliação: {error}"},
            "final_decision": "WARNING"
        }
