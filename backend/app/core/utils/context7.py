import re
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

def clean_context7_violations(content: str, context_type: str = "generic") -> str:
    """
    Remove JSON bruto e estruturas técnicas das respostas (Context7 Storytelling).
    Garanti que a resposta seja narrativa natural.

    Args:
        content: Conteúdo a limpar
        context_type: Tipo de contexto ("chart", "data", "analysis", "generic")

    Returns:
        Conteúdo limpo com narrativa natural
    """
    if not isinstance(content, str) or not content:
        return content

    original_content = content
    cleaned = content

    # 1. Detectar e remover markdown JSON blocks (```json...```)
    markdown_json_pattern = r'```json\s*\n(.*?)\n```'
    if re.search(markdown_json_pattern, cleaned, re.DOTALL):
        logger.warning("[CONTEXT7] Detectado markdown JSON block. Removendo.")
        cleaned = re.sub(markdown_json_pattern, "", cleaned, flags=re.DOTALL)

    # 2. Detectar e remover blocos JSON inline grandes (chart specs, etc)
    # Padrão para detectar objetos JSON com "data" e "layout" (Plotly)
    plotly_json_pattern = r'\{[\s\S]*?"data"[\s\S]*?"layout"[\s\S]*?\}'
    if re.search(plotly_json_pattern, cleaned):
        logger.warning("[CONTEXT7] Detectado Plotly JSON inline. Removendo.")
        cleaned = re.sub(plotly_json_pattern, "", cleaned)

    # 3. Detectar JSON puro no início (objeto ou array)
    stripped = cleaned.strip()
    if (stripped.startswith("{") or stripped.startswith("[")) and len(stripped) > 50:
        # Tentar validar se é JSON
        try:
            json.loads(stripped)
            logger.warning("[CONTEXT7] Detectado JSON puro. Substituindo com narrativa.")
            cleaned = ""  # Limpar completamente, será substituído abaixo
        except json.JSONDecodeError:
            pass  # Não é JSON válido, manter

    # 4. Se ficou vazio ou muito curto, substituir com narrativa contextual
    cleaned = cleaned.strip()
    if not cleaned or len(cleaned) < 10:
        if context_type == "chart":
            cleaned = "Aqui está o gráfico que você solicitou."
        elif context_type == "data":
            cleaned = "Recuperei os dados solicitados e organizei para você."
        elif context_type == "analysis":
            cleaned = "Com base nos dados disponíveis, aqui está a análise:"
        else:
            cleaned = "Processado com sucesso."

        logger.info(f"[CONTEXT7] Substituído com narrativa contextual ({context_type})")

    # 5. Se mudou, logar a transformação
    if cleaned != original_content:
        logger.info(f"[CONTEXT7] Limpeza aplicada. Antes: {len(original_content)} chars, Depois: {len(cleaned)} chars")

    return cleaned
