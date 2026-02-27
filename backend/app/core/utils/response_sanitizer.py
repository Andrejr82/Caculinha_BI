import json
import logging
import re

logger = logging.getLogger(__name__)


def clean_response_violations(content: str, context_type: str = "generic") -> str:
    """
    Remove blocos técnicos/JSON bruto para manter narrativa legível ao usuário.

    Args:
        content: Conteúdo a limpar
        context_type: "chart", "data", "analysis" ou "generic"
    """
    if not isinstance(content, str) or not content:
        return content

    original_content = content
    cleaned = content

    # 1) Remove markdown JSON block (```json ... ```)
    markdown_json_pattern = r"```json\s*\n(.*?)\n```"
    if re.search(markdown_json_pattern, cleaned, re.DOTALL):
        logger.warning("[NARRATIVE] Markdown JSON block detectado. Removendo.")
        cleaned = re.sub(markdown_json_pattern, "", cleaned, flags=re.DOTALL)

    # 2) Remove blocos grandes com formato Plotly inline
    plotly_json_pattern = r"\{[\s\S]*?\"data\"[\s\S]*?\"layout\"[\s\S]*?\}"
    if re.search(plotly_json_pattern, cleaned):
        logger.warning("[NARRATIVE] Plotly JSON inline detectado. Removendo.")
        cleaned = re.sub(plotly_json_pattern, "", cleaned)

    # 3) Se o conteúdo inteiro parece JSON puro, limpar
    stripped = cleaned.strip()
    if (stripped.startswith("{") or stripped.startswith("[")) and len(stripped) > 50:
        try:
            json.loads(stripped)
            logger.warning("[NARRATIVE] JSON puro detectado. Substituindo por narrativa.")
            cleaned = ""
        except json.JSONDecodeError:
            pass

    # 4) Fallback narrativo contextual
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
        logger.info(f"[NARRATIVE] Texto substituído com contexto ({context_type}).")

    if cleaned != original_content:
        logger.info(
            f"[NARRATIVE] Limpeza aplicada. Antes={len(original_content)} chars, Depois={len(cleaned)} chars"
        )

    return cleaned

