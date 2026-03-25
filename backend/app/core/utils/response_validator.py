"""
Response Validator - Valida respostas do agente para detectar erros e alucinações
Usa técnicas de verificação para melhorar precisão
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Resultado da validação de resposta."""
    is_valid: bool
    confidence: float  # 0.0 a 1.0
    issues: List[str]
    suggestions: List[str]
    corrected_response: Optional[str] = None
    should_block: bool = False
    block_reason: Optional[str] = None


class ResponseValidator:
    """
    Valida respostas do ChatBI para detectar:
    - Alucinações (dados inventados)
    - Inconsistências numéricas
    - Referências a dados inexistentes
    - Erros de formatação
    """
    
    # Colunas reais do admmat.parquet
    VALID_COLUMNS = {
        "id", "UNE", "PRODUTO", "TIPO", "UNE_NOME", "NOME", "EMBALAGEM",
        "NOMESEGMENTO", "NOMECATEGORIA", "NOMEFABRICANTE", "SITUACAO",
        "ESTOQUE_UNE", "ESTOQUE_LV", "ESTOQUE_CD", "VENDA_30DD",
        "PRECO_VENDA", "PRECO_CUSTO", "PICKLIST_SITUACAO",
        "ULTIMA_VENDA_DATA_UNE", "created_at", "updated_at",
        # Campos derivados de apresentação (não internos sensíveis)
        "TOTAL_VENDAS", "VALOR", "ITENS", "VENDA_30DD_TOTAL", "ESTOQUE_UNE_TOTAL"
    }
    
    # Palavras que indicam possível alucinação
    HALLUCINATION_INDICATORS = [
        "possivelmente", "provavelmente", "talvez", "não tenho certeza",
        "acredito que", "parece que", "pode ser", "imagino que"
    ]
    
    # Padrões de erro conhecidos
    ERROR_PATTERNS = [
        r"erro\s+ao\s+consultar",
        r"não\s+foi\s+possível",
        r"falha\s+na\s+consulta",
        r"coluna.*não\s+encontrada",
        r"dados\s+não\s+encontrados",
    ]
    
    def __init__(self):
        self.validation_count = 0
        self.error_count = 0
    
    def validate(
        self,
        response: Dict[str, Any],
        query: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Valida uma resposta do agente.
        
        Args:
            response: Resposta do agente
            query: Pergunta original do usuário
            
        Returns:
            ValidationResult com status e detalhes
        """
        self.validation_count += 1
        issues = []
        suggestions = []
        confidence = 1.0
        should_block = False
        block_reason = None
        validation_context = context if isinstance(context, dict) else {}
        
        # Extrair texto da resposta
        response_text = self._extract_text(response)
        
        # 1. Verificar se resposta está vazia
        if not response_text or len(response_text.strip()) < 10:
            issues.append("Resposta muito curta ou vazia")
            suggestions.append("Reformule a pergunta de forma mais específica")
            confidence -= 0.5
        
        # 2. Verificar indicadores de alucinação
        hallucination_score = self._check_hallucination(response_text)
        if hallucination_score > 0.3:
            issues.append(f"Possível incerteza detectada (score: {hallucination_score:.2f})")
            suggestions.append("Verifique os dados retornados")
            confidence -= hallucination_score * 0.3
        
        # 3. Verificar padrões de erro
        if self._has_error_pattern(response_text):
            issues.append("Padrão de erro detectado na resposta")
            suggestions.append("Verifique os parâmetros da consulta")
            confidence -= 0.3
        
        # 4. Validar referências a colunas
        invalid_cols = self._check_column_references(response_text)
        if invalid_cols:
            issues.append(f"Referências a colunas possivelmente inválidas: {', '.join(invalid_cols)}")
            suggestions.append(f"Colunas válidas incluem: UNE, PRODUTO, NOME, ESTOQUE_UNE, VENDA_30DD")
            confidence -= 0.2
        
        # 5. Verificar consistência numérica
        numeric_issues = self._check_numeric_consistency(response_text)
        if numeric_issues:
            issues.extend(numeric_issues)
            confidence -= 0.1 * len(numeric_issues)

        semantic_result = self._validate_semantic_contract(
            response=response,
            query=query,
            context=validation_context,
        )
        if semantic_result["issues"]:
            issues.extend(semantic_result["issues"])
        if semantic_result["suggestions"]:
            suggestions.extend(semantic_result["suggestions"])
        confidence -= semantic_result["confidence_penalty"]
        should_block = semantic_result["should_block"]
        block_reason = semantic_result["block_reason"]
        
        # Garantir que confidence está entre 0 e 1
        confidence = max(0.0, min(1.0, confidence))
        
        is_valid = len(issues) == 0 and confidence >= 0.7
        
        if not is_valid:
            self.error_count += 1
            logger.warning(f"Resposta inválida: {issues}")
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions
            ,
            should_block=should_block,
            block_reason=block_reason,
        )

    def _validate_semantic_contract(
        self,
        *,
        response: Dict[str, Any],
        query: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        issues: List[str] = []
        suggestions: List[str] = []
        confidence_penalty = 0.0
        should_block = False
        block_reason: Optional[str] = None

        expected_capability = str(context.get("expected_capability") or "").strip().lower()
        actual_capability = str(context.get("actual_capability") or "").strip().lower()
        response_mode = str(context.get("mode") or "").strip().lower()
        response_source = str(context.get("source") or "").strip().lower()
        has_visual_payload = bool(context.get("has_visual_payload"))
        has_dashboard_payload = bool(context.get("has_dashboard_payload"))
        has_table_payload = bool(context.get("has_table_payload"))
        has_export_payload = bool(context.get("has_export_payload"))
        citations_count = int(context.get("citations_count") or 0)
        no_data_detected = bool(context.get("no_data_detected"))
        has_evidence = bool(context.get("has_evidence"))

        if (
            expected_capability
            and actual_capability
            and not self._capabilities_are_compatible(expected_capability, actual_capability)
        ):
            issues.append(
                f"Capacidade incoerente com a intenção da pergunta: esperado={expected_capability}, retornado={actual_capability}"
            )
            suggestions.append("Responder usando a capability alinhada à intenção do usuário.")
            confidence_penalty += 0.45
            should_block = True
            block_reason = "capability_mismatch"

        if expected_capability == "visualization" and not has_visual_payload and not no_data_detected:
            issues.append("Pedido de gráfico sem payload visual na resposta final.")
            suggestions.append("Gerar chart_data ou dashboard_spec antes de responder ao usuário.")
            confidence_penalty += 0.55
            should_block = True
            block_reason = block_reason or "missing_visual_payload"

        if expected_capability == "dashboard" and not has_dashboard_payload and not no_data_detected:
            issues.append("Pedido de dashboard sem dashboard_spec na resposta final.")
            suggestions.append("Gerar dashboard_spec consistente com a solicitação.")
            confidence_penalty += 0.55
            should_block = True
            block_reason = block_reason or "missing_dashboard_payload"

        if expected_capability == "table" and not has_table_payload and not no_data_detected:
            issues.append("Pedido de tabela sem payload tabular na resposta final.")
            suggestions.append("Gerar table_data consistente com a solicitação ou responder no_data de forma honesta.")
            confidence_penalty += 0.50
            should_block = True
            block_reason = block_reason or "missing_table_payload"

        if expected_capability == "export" and not has_export_payload and not no_data_detected:
            issues.append("Pedido de exportação sem artefato ou metadata de export válida.")
            suggestions.append("Gerar automation_request/artifact compatível com exportação antes de responder.")
            confidence_penalty += 0.50
            should_block = True
            block_reason = block_reason or "missing_export_payload"

        if expected_capability == "market_research" and citations_count <= 0 and not no_data_detected:
            issues.append("Pesquisa de mercado sem citações ou evidências públicas.")
            suggestions.append("Incluir citações válidas ou responder explicitamente que não houve evidência suficiente.")
            confidence_penalty += 0.50
            should_block = True
            block_reason = block_reason or "missing_market_evidence"

        if response_mode in {"attachment_basket_pipeline", "dataset_basket_pipeline"} and expected_capability not in {"calculation", ""}:
            issues.append("Pipeline de basket respondeu a uma intenção não relacionada a cálculo/cesta.")
            suggestions.append("Descartar o pipeline especializado e priorizar o fluxo compatível com a pergunta.")
            confidence_penalty += 0.60
            should_block = True
            block_reason = block_reason or "wrong_specialized_pipeline"

        if no_data_detected and has_evidence:
            issues.append("Mensagem de sem dados retornada apesar de haver evidências ou payload útil.")
            suggestions.append("Substituir a resposta por uma saída baseada nas evidências disponíveis.")
            confidence_penalty += 0.40
            should_block = True
            block_reason = block_reason or "false_no_data"

        if expected_capability == "calculation" and actual_capability == "market_research":
            issues.append("Resposta de pesquisa de mercado retornada para uma pergunta de cálculo.")
            suggestions.append("Priorizar o pipeline analítico ou de cálculo em vez de pesquisa pública.")
            confidence_penalty += 0.40
            should_block = True
            block_reason = block_reason or "wrong_analysis_type"

        return {
            "issues": issues,
            "suggestions": suggestions,
            "confidence_penalty": confidence_penalty,
            "should_block": should_block,
            "block_reason": block_reason,
        }

    def _capabilities_are_compatible(self, expected_capability: str, actual_capability: str) -> bool:
        compatibility_map = {
            "data_query": {"data_query", "table"},
            "table": {"table", "data_query"},
            "visualization": {"visualization"},
            "dashboard": {"dashboard"},
            "export": {"export"},
            "market_research": {"market_research"},
            "calculation": {"calculation", "table"},
        }
        allowed = compatibility_map.get(expected_capability, {expected_capability})
        return actual_capability in allowed
    
    def _extract_text(self, response: Dict[str, Any]) -> str:
        """Extrai texto da resposta do agente."""
        if isinstance(response, str):
            return response
        
        # Tentar diferentes formatos de resposta
        text = response.get("result", "")
        if isinstance(text, dict):
            text = text.get("mensagem", "") or str(text)
        elif not isinstance(text, str):
            text = str(text)
        
        return text
    
    def _check_hallucination(self, text: str) -> float:
        """Verifica indicadores de alucinação."""
        text_lower = text.lower()
        count = 0
        
        for indicator in self.HALLUCINATION_INDICATORS:
            if indicator in text_lower:
                count += 1
        
        # Normalizar score
        return min(1.0, count / 3)
    
    def _has_error_pattern(self, text: str) -> bool:
        """Verifica padrões de erro conhecidos."""
        text_lower = text.lower()
        
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _check_column_references(self, text: str) -> List[str]:
        """Verifica referências a colunas potencialmente inválidas."""
        # Buscar padrões que parecem nomes de colunas
        pattern = r'\b([A-Z][A-Z0-9_]{2,30})\b'
        matches = re.findall(pattern, text)
        
        invalid = []
        for match in matches:
            # Ignorar palavras comuns que não são colunas
            if match in {"OK", "NULL", "TRUE", "FALSE", "AND", "OR", "NOT"}:
                continue
            
            # Verificar se parece uma coluna mas não está na lista válida
            if "_" in match or match.isupper():
                if match not in self.VALID_COLUMNS:
                    invalid.append(match)
        
        return invalid[:3]  # Limitar a 3 para não poluir
    
    def _check_numeric_consistency(self, text: str) -> List[str]:
        """Verifica consistência de valores numéricos."""
        issues = []
        
        # Buscar números muito grandes que podem ser erros
        pattern = r'\b(\d{10,})\b'
        large_numbers = re.findall(pattern, text)
        
        for num in large_numbers:
            if len(num) > 15:
                issues.append(f"Número muito grande detectado: pode ser erro")
                break
        
        # Buscar valores negativos onde não deveria haver
        if re.search(r'estoque.*-\d+|vendas.*-\d+', text.lower()):
            issues.append("Valor negativo detectado em campo que deveria ser positivo")
        
        return issues
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de validação."""
        error_rate = (self.error_count / self.validation_count * 100) if self.validation_count > 0 else 0
        
        return {
            "total_validations": self.validation_count,
            "total_errors": self.error_count,
            "error_rate": f"{error_rate:.1f}%",
            "valid_columns_count": len(self.VALID_COLUMNS),
        }


# Instância global
_validator: Optional[ResponseValidator] = None


def get_validator() -> ResponseValidator:
    """Retorna instância singleton do validador."""
    global _validator
    if _validator is None:
        _validator = ResponseValidator()
    return _validator


def validate_response(
    response: Dict[str, Any],
    query: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> ValidationResult:
    """Valida resposta do agente."""
    return get_validator().validate(response, query, context=context)


def validator_stats() -> Dict[str, Any]:
    """Retorna estatísticas do validador."""
    return get_validator().get_stats()
