"""
Compatibilidade retroativa.

Historicamente, este projeto chamou o sanitizador narrativo de "context7".
Para evitar confusão com o framework externo Context7, use
`backend.app.core.utils.response_sanitizer.clean_response_violations`.
"""

from backend.app.core.utils.response_sanitizer import clean_response_violations


def clean_context7_violations(content: str, context_type: str = "generic") -> str:
    """Alias legada para não quebrar importações antigas."""
    return clean_response_violations(content=content, context_type=context_type)
