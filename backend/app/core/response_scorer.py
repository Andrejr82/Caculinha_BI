"""
Response Scorer - Automatic response quality evaluation

Scores every agent response based on:
- Helpfulness (structure, completeness)
- Groundedness (data citation, specificity)
- Performance (latency)
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ResponseScorer:
    """
    Automatic scoring of agent responses.
    
    Computes deterministic scores without using LLM tokens.
    """
    
    # Scoring thresholds
    MIN_RESPONSE_LENGTH = 50
    GOOD_RESPONSE_LENGTH = 200
    MAX_LATENCY_MS = 5000  # 5 seconds
    
    def score(
        self,
        prompt: str,
        response: str,
        latency_ms: float = 0,
        retrieved_docs: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Score a response based on multiple dimensions.
        
        Args:
            prompt: User's original question
            response: Agent's response
            latency_ms: Response latency in milliseconds
            retrieved_docs: List of retrieved document IDs (for RAG)
            context: Additional context
            
        Returns:
            Evaluation result with scores and reasons
        """
        scores = {}
        reasons = []
        
        # 1. Helpfulness Score (0-100)
        helpfulness = self._score_helpfulness(response)
        scores["helpfulness"] = helpfulness["score"]
        reasons.extend(helpfulness["reasons"])
        
        # 2. Groundedness Score (0-100)
        groundedness = self._score_groundedness(response, retrieved_docs)
        scores["groundedness"] = groundedness["score"]
        reasons.extend(groundedness["reasons"])
        
        # 3. Correctness Proxy (0-100)
        correctness = self._score_correctness(response)
        scores["correctness"] = correctness["score"]
        reasons.extend(correctness["reasons"])
        
        # 4. Performance Score (0-100)
        performance = self._score_performance(latency_ms)
        scores["performance"] = performance["score"]
        reasons.extend(performance["reasons"])
        
        # Calculate weighted overall score
        overall = (
            scores["helpfulness"] * 0.35 +
            scores["groundedness"] * 0.25 +
            scores["correctness"] * 0.25 +
            scores["performance"] * 0.15
        )
        
        return {
            "overall_score": round(overall, 1),
            "dimension_scores": scores,
            "reasons": reasons,
            "latency_ms": latency_ms,
            "response_length": len(response),
            "scored_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _score_helpfulness(self, response: str) -> Dict[str, Any]:
        """Score based on structure and completeness."""
        score = 50  # Base score
        reasons = []
        
        # Length check
        if len(response) < self.MIN_RESPONSE_LENGTH:
            score -= 30
            reasons.append("Resposta muito curta")
        elif len(response) >= self.GOOD_RESPONSE_LENGTH:
            score += 20
            reasons.append("Resposta detalhada")
        
        # Structure indicators
        has_numbers = bool(re.search(r'\d+', response))
        has_sections = bool(re.search(r'(##|###|\*\*|\n-|\n\d\.)', response))
        has_lists = bool(re.search(r'(\n[-*]\s|\n\d+\.\s)', response))
        
        if has_numbers:
            score += 10
            reasons.append("Inclui dados numéricos")
        if has_sections:
            score += 10
            reasons.append("Bem estruturada")
        if has_lists:
            score += 10
        
        return {"score": min(100, max(0, score)), "reasons": reasons}
    
    def _score_groundedness(
        self,
        response: str,
        retrieved_docs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Score based on data grounding and specificity."""
        score = 60  # Base score
        reasons = []
        
        # Check for specific values/data
        has_percentages = bool(re.search(r'\d+([.,]\d+)?%', response))
        has_currency = bool(re.search(r'R\$\s*[\d.,]+', response))
        has_dates = bool(re.search(r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}', response))
        has_quantities = bool(re.search(r'\d+\s*(unidades|itens|produtos|lojas)', response, re.I))
        
        if has_percentages:
            score += 10
            reasons.append("Inclui percentuais")
        if has_currency:
            score += 10
            reasons.append("Inclui valores monetários")
        if has_dates:
            score += 5
        if has_quantities:
            score += 10
            reasons.append("Inclui quantidades específicas")
        
        # RAG grounding
        if retrieved_docs and len(retrieved_docs) > 0:
            score += 15
            reasons.append(f"Baseada em {len(retrieved_docs)} documentos")
        
        return {"score": min(100, max(0, score)), "reasons": reasons}
    
    def _score_correctness(self, response: str) -> Dict[str, Any]:
        """Score based on format validity and non-empty content."""
        score = 70  # Base score
        reasons = []
        
        # Check for error indicators
        error_patterns = [
            r'erro|error|falha|failed',
            r'não foi possível|could not',
            r'não encontr|not found',
            r'indisponível|unavailable'
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, response, re.I):
                score -= 20
                reasons.append("Contém indicadores de erro")
                break
        
        # Check for actionable content
        if any(word in response.lower() for word in ['recomendo', 'sugiro', 'deve', 'considere']):
            score += 15
            reasons.append("Inclui recomendações")
        
        # JSON in response (usually bad for user-facing)
        if response.strip().startswith('{') or '```json' in response:
            score -= 10
            reasons.append("Contém JSON bruto")
        
        return {"score": min(100, max(0, score)), "reasons": reasons}
    
    def _score_performance(self, latency_ms: float) -> Dict[str, Any]:
        """Score based on response latency."""
        if latency_ms <= 0:
            return {"score": 50, "reasons": ["Latência não medida"]}
        
        if latency_ms <= 500:
            return {"score": 100, "reasons": ["Resposta muito rápida"]}
        elif latency_ms <= 1000:
            return {"score": 90, "reasons": ["Resposta rápida"]}
        elif latency_ms <= 2000:
            return {"score": 75, "reasons": []}
        elif latency_ms <= self.MAX_LATENCY_MS:
            return {"score": 50, "reasons": ["Resposta lenta"]}
        else:
            return {"score": 25, "reasons": ["Resposta muito lenta"]}


# Global singleton
response_scorer = ResponseScorer()


def score_and_save_response(
    request_id: str,
    user_id: str,
    tenant_id: str,
    prompt: str,
    response: str,
    latency_ms: float = 0,
    retrieved_doc_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Score a response and save the evaluation.
    
    This is the main entry point for automatic scoring.
    """
    from backend.app.core.evaluations_repository import evaluations_repo
    
    # Score the response
    eval_result = response_scorer.score(
        prompt=prompt,
        response=response,
        latency_ms=latency_ms,
        retrieved_docs=retrieved_doc_ids
    )
    
    # Build evaluation record
    evaluation = {
        "request_id": request_id,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "prompt": prompt[:500] if prompt else "",  # Truncate for storage
        "response": response[:2000] if response else "",  # Truncate for storage
        "overall_score": eval_result["overall_score"],
        "dimension_scores": eval_result["dimension_scores"],
        "reasons": eval_result["reasons"],
        "latency_ms": latency_ms,
        "retrieved_doc_ids": retrieved_doc_ids or [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Save to repository
    evaluations_repo.save(evaluation)
    
    logger.info(f"Response scored: request_id={request_id}, score={eval_result['overall_score']}")
    
    return eval_result
