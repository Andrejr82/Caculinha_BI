from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class OutputValidationResult:
    is_safe: bool
    reason: str
    detected_language: str


SQL_BLOCKLIST = [
    r"\bdrop\s+table\b",
    r"\btruncate\s+table\b",
    r"\balter\s+table\b",
    r"\bdelete\s+from\b",
    r"\bupdate\s+\w+\s+set\b",
    r"\bexec\s*\(",
    r"\bxp_cmdshell\b",
]

PYTHON_BLOCKLIST = [
    r"\bos\.system\s*\(",
    r"\bsubprocess\.",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bopen\s*\(",
    r"\b__import__\s*\(",
]


def _detect_language(text: str) -> str:
    lower = (text or "").lower()
    if "```sql" in lower or "select " in lower:
        return "sql"
    if "```python" in lower or "import " in lower or "def " in lower:
        return "python"
    return "text"


def _contains_blocked_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def validate_playground_output(content: str) -> OutputValidationResult:
    text = content or ""
    detected_language = _detect_language(text)

    if detected_language == "sql" and _contains_blocked_pattern(text, SQL_BLOCKLIST):
        return OutputValidationResult(
            is_safe=False,
            reason="Conteúdo SQL contém instruções potencialmente destrutivas.",
            detected_language=detected_language,
        )

    if detected_language == "python" and _contains_blocked_pattern(text, PYTHON_BLOCKLIST):
        return OutputValidationResult(
            is_safe=False,
            reason="Conteúdo Python contém chamadas potencialmente inseguras.",
            detected_language=detected_language,
        )

    return OutputValidationResult(
        is_safe=True,
        reason="Conteúdo validado com política básica de segurança.",
        detected_language=detected_language,
    )
