"""
Prompts Module - Centralized System Prompts

Este módulo centraliza todos os prompts do sistema para fácil manutenção.
"""

from .master_prompt import (
    MASTER_PROMPT,
    get_system_prompt,
    get_few_shot_examples,
)

__all__ = [
    'MASTER_PROMPT',
    'get_system_prompt',
    'get_few_shot_examples',
]
