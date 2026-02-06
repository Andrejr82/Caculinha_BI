"""
Ferramenta de teste MÍNIMA para isolar problema MALFORMED_FUNCTION_CALL.
Seguindo metodologia Debugger: Binary Search para encontrar causa raiz.
"""
from typing import Dict, Any
from langchain.tools import tool

@tool
def teste_minimal(mensagem: str) -> str:
    """
    Ferramenta de teste simples.
    
    Args:
        mensagem: Uma mensagem de texto simples.
    
    Returns:
        Echo da mensagem.
    """
    return f"Echo: {mensagem}"
