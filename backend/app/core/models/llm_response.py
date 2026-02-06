"""
Modelos Pydantic para Structured Output da LLM.

Implementa melhores práticas 2024-2025:
- Constrained Decoding
- Grammar-Guided Generation
- Validation Guardrails
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class RespostaBI(BaseModel):
    """
    Estrutura obrigatória para respostas do Caçulinha BI.
    
    Garante que LLM SEMPRE mencione filtros aplicados e siga formato estruturado.
    """
    
    filtros_mencionados: List[str] = Field(
        ...,
        min_items=0,
        description="Lista de filtros mencionados explicitamente na resposta (ex: ['UNE 3', 'Período: 30 dias'])"
    )
    
    resumo_executivo: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Resumo executivo que DEVE mencionar filtros aplicados se houver"
    )
    
    analise_detalhada: str = Field(
        ...,
        min_length=10,
        description="Análise detalhada dos dados fornecidos"
    )
    
    insights: List[str] = Field(
        default_factory=list,
        min_items=1,
        max_items=5,
        description="Insights principais (1-5 itens)"
    )
    
    recomendacoes: List[str] = Field(
        default_factory=list,
        max_items=5,
        description="Recomendações de ação (opcional)"
    )
    
    dados_citados: bool = Field(
        default=True,
        description="Indica se a resposta cita dados do contexto fornecido"
    )
    
    @validator('resumo_executivo')
    def validate_resumo(cls, v, values):
        """Valida que resumo menciona filtros se houver"""
        # Esta validação será feita em runtime no guardrail
        return v
    
    @validator('insights')
    def validate_insights(cls, v):
        """Valida que insights não estão vazios"""
        if not v:
            raise ValueError("Pelo menos 1 insight é obrigatório")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "filtros_mencionados": ["UNE 3", "Período: 30 dias"],
                "resumo_executivo": "Análise de vendas da UNE 3 nos últimos 30 dias. A UNE 3 apresentou faturamento de R$ 150.000.",
                "analise_detalhada": "A UNE 3 demonstra performance sólida com destaque para o segmento de Papelaria...",
                "insights": [
                    "Segmento de Papelaria lidera com 35% do faturamento",
                    "Produto X é o mais vendido",
                    "Estoque adequado para demanda"
                ],
                "recomendacoes": [
                    "Manter níveis de estoque atuais",
                    "Expandir mix de produtos no segmento líder"
                ],
                "dados_citados": True
            }
        }


class ValidationResult(BaseModel):
    """Resultado da validação de resposta da LLM"""
    
    is_valid: bool = Field(..., description="Se a resposta passou na validação")
    errors: List[str] = Field(default_factory=list, description="Lista de erros encontrados")
    warnings: List[str] = Field(default_factory=list, description="Lista de avisos")
    corrected_response: Optional[RespostaBI] = Field(None, description="Resposta corrigida se houver erros")
    
    def has_errors(self) -> bool:
        """Verifica se há erros"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Verifica se há avisos"""
        return len(self.warnings) > 0


def validate_response_guardrails(
    response: RespostaBI,
    intent: Any,
    context: str
) -> ValidationResult:
    """
    Validation Guardrails - Valida resposta da LLM antes de retornar ao usuário.
    
    Implementa melhores práticas 2024-2025:
    - Verifica se filtros foram mencionados
    - Detecta hallucinations
    - Garante que dados foram citados
    
    Args:
        response: Resposta estruturada da LLM
        intent: QueryIntent original
        context: Contexto fornecido à LLM
    
    Returns:
        ValidationResult com status e possíveis correções
    """
    errors = []
    warnings = []
    corrected = None
    
    # Validação 1: Filtros explícitos devem ser mencionados
    if hasattr(intent, 'entities') and intent.entities:
        # Verificar UNE
        if intent.entities.get('une_explicit'):
            une = intent.entities['une']
            une_mentioned = any(
                f"UNE {une}" in text or f"une {une}" in text.lower()
                for text in [response.resumo_executivo, response.analise_detalhada]
            )
            
            if not une_mentioned:
                errors.append(f"Filtro UNE {une} não foi mencionado explicitamente")
                # Corrigir automaticamente
                corrected = response.copy()
                corrected.resumo_executivo = f"**Análise da UNE {une}:** " + corrected.resumo_executivo
                corrected.filtros_mencionados.append(f"UNE {une}")
                logger.warning(f"[GUARDRAIL] Filtro UNE {une} não mencionado - corrigido automaticamente")
        
        # Verificar outros filtros
        for key in ['segmento', 'produto', 'periodo']:
            if intent.entities.get(key):
                filter_value = intent.entities[key]
                if filter_value not in response.filtros_mencionados:
                    warnings.append(f"Filtro {key}={filter_value} não está em filtros_mencionados")
    
    # Validação 2: Dados citados
    if not response.dados_citados:
        warnings.append("Resposta não cita dados do contexto")
    
    # Validação 3: Hallucination check básico
    # Verificar se números mencionados existem no contexto
    import re
    numbers_in_response = re.findall(r'R\$\s*([\d,.]+)', response.resumo_executivo + response.analise_detalhada)
    if numbers_in_response and context:
        # Verificação simplificada: pelo menos alguns números devem estar no contexto
        numbers_in_context = re.findall(r'([\d,.]+)', context)
        if not any(num in numbers_in_context for num in numbers_in_response[:3]):
            warnings.append("Possível hallucination: números mencionados não encontrados no contexto")
    
    # Validação 4: Insights não vazios
    if not response.insights:
        errors.append("Nenhum insight fornecido")
    
    is_valid = len(errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        corrected_response=corrected if errors else None
    )
