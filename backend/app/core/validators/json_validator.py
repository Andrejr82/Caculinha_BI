"""
JSON Validator - Validação de Respostas LLM

Valida que as respostas da LLM seguem o schema JSON Protocol v3.0.
"""

import json
import jsonschema
from typing import Dict, List, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Carregar schema do arquivo
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "json_schema_bi_protocol.json"

try:
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        BI_PROTOCOL_SCHEMA = json.load(f)
    logger.info(f"[OK] Schema JSON carregado: {SCHEMA_PATH}")
except FileNotFoundError:
    logger.error(f"[ERROR] Schema não encontrado: {SCHEMA_PATH}")
    BI_PROTOCOL_SCHEMA = None


def validate_llm_response(response_json: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valida resposta da LLM contra o schema BI_PROTOCOL_V3.0.
    
    Args:
        response_json: Dicionário com a resposta da LLM
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    
    Examples:
        >>> response = {"protocol_version": "BI_PROTOCOL_V3.0", ...}
        >>> is_valid, errors = validate_llm_response(response)
        >>> if not is_valid:
        ...     print(f"Erros: {errors}")
    """
    if BI_PROTOCOL_SCHEMA is None:
        logger.warning("Schema não disponível, pulando validação")
        return True, []
    
    errors = []
    
    try:
        # Validar contra schema JSON
        jsonschema.validate(instance=response_json, schema=BI_PROTOCOL_SCHEMA)
        
        # Validações adicionais de negócio
        
        # 1. Verificar protocol_version
        if response_json.get("protocol_version") != "BI_PROTOCOL_V3.0":
            errors.append(
                f"protocol_version inválido: '{response_json.get('protocol_version')}'. "
                "Esperado: 'BI_PROTOCOL_V3.0'"
            )
        
        # 2. Verificar analise_maturidade
        valid_maturities = ["DESCRITIVA", "DIAGNOSTICA", "PREDITIVA", "PRESCRITIVA", "OPERACIONAL"]
        maturidade = response_json.get("analise_maturidade")
        if maturidade not in valid_maturities:
            errors.append(
                f"analise_maturidade inválido: '{maturidade}'. "
                f"Esperado um de: {valid_maturities}"
            )
        
        # 3. Verificar se resumo_executivo não está vazio
        resumo = response_json.get("resumo_executivo", "")
        if not resumo or len(resumo.strip()) < 10:
            errors.append("resumo_executivo muito curto ou vazio (mínimo 10 caracteres)")
        
        # 4. Verificar se analise_detalhada não está vazia
        analise = response_json.get("analise_detalhada", "")
        if not analise or len(analise.strip()) < 50:
            errors.append("analise_detalhada muito curta ou vazia (mínimo 50 caracteres)")
        
        # 5. Se análise é PREDITIVA ou PRESCRITIVA, recomendacao_prescritiva é obrigatória
        if maturidade in ["PREDITIVA", "PRESCRITIVA"]:
            recomendacao = response_json.get("recomendacao_prescritiva")
            if not recomendacao:
                errors.append(
                    f"recomendacao_prescritiva é obrigatória para análises {maturidade}"
                )
            elif not recomendacao.get("acao_sugerida"):
                errors.append("recomendacao_prescritiva.acao_sugerida não pode estar vazia")
            elif not recomendacao.get("justificativa"):
                errors.append("recomendacao_prescritiva.justificativa não pode estar vazia")
        
        # 6. Verificar dados_suporte se presente
        dados_suporte = response_json.get("dados_suporte", [])
        if dados_suporte:
            for idx, dado in enumerate(dados_suporte):
                if not dado.get("metrica"):
                    errors.append(f"dados_suporte[{idx}].metrica não pode estar vazio")
                if not dado.get("valor"):
                    errors.append(f"dados_suporte[{idx}].valor não pode estar vazio")
        
        # 7. Verificar visualizacao se presente
        visualizacao = response_json.get("visualizacao")
        if visualizacao:
            if "data" not in visualizacao:
                errors.append("visualizacao.data é obrigatório quando visualizacao está presente")
            if "layout" not in visualizacao:
                errors.append("visualizacao.layout é obrigatório quando visualizacao está presente")
        
        if errors:
            logger.warning(f"[WARNING] Validação falhou com {len(errors)} erros")
            return False, errors
        
        logger.info("[OK] Resposta validada com sucesso")
        return True, []
    
    except jsonschema.ValidationError as e:
        error_msg = f"Erro de schema JSON: {e.message} (path: {'.'.join(str(p) for p in e.path)})"
        logger.error(f"[ERROR] {error_msg}")
        return False, [error_msg]
    
    except Exception as e:
        error_msg = f"Erro inesperado na validação: {str(e)}"
        logger.error(f"[ERROR] {error_msg}", exc_info=True)
        return False, [error_msg]


def validate_and_fix_response(response_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida e tenta corrigir automaticamente problemas comuns na resposta.
    
    Args:
        response_json: Resposta da LLM
    
    Returns:
        Resposta corrigida (ou original se não houver correções)
    """
    # Fazer uma cópia para não modificar o original
    fixed = response_json.copy()
    
    # Correção 1: Adicionar protocol_version se ausente
    if "protocol_version" not in fixed:
        fixed["protocol_version"] = "BI_PROTOCOL_V3.0"
        logger.info("[DEBUG] Adicionado protocol_version automaticamente")
    
    # Correção 2: Garantir campos obrigatórios mínimos
    if "resumo_executivo" not in fixed or not fixed["resumo_executivo"]:
        fixed["resumo_executivo"] = "Análise concluída. Verifique os detalhes abaixo."
        logger.warning("[DEBUG] resumo_executivo estava vazio, adicionado texto padrão")
    
    if "analise_detalhada" not in fixed or not fixed["analise_detalhada"]:
        fixed["analise_detalhada"] = "Análise detalhada não disponível."
        logger.warning("[DEBUG] analise_detalhada estava vazia, adicionado texto padrão")
    
    if "analise_maturidade" not in fixed:
        fixed["analise_maturidade"] = "DESCRITIVA"
        logger.info("[DEBUG] Definido analise_maturidade como DESCRITIVA (padrão)")
    
    # Correção 3: Inicializar arrays vazios se ausentes
    if "dados_suporte" not in fixed:
        fixed["dados_suporte"] = []
    
    if "ferramentas_utilizadas" not in fixed:
        fixed["ferramentas_utilizadas"] = []
    
    return fixed


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extrai JSON de texto que pode conter markdown ou texto adicional.
    
    Args:
        text: Texto contendo JSON (possivelmente com markdown)
    
    Returns:
        Dicionário extraído do JSON
    
    Raises:
        json.JSONDecodeError: Se não conseguir extrair JSON válido
    """
    # Tentar parsear diretamente
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Tentar encontrar JSON entre ```json e ```
    import re
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Tentar encontrar qualquer objeto JSON no texto
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise json.JSONDecodeError("Não foi possível extrair JSON válido do texto", text, 0)
