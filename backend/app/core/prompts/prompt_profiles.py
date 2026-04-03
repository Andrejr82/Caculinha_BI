"""
Prompt profile helpers for the Caçula BI assistant.

Keep prompt assembly deterministic and compact:
- select high-signal few-shot examples
- format examples without exposing chain-of-thought
- inject domain playbooks for the main retail workflows
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List


DOMAIN_PLAYBOOKS: List[Dict[str, Any]] = [
    {
        "title": "Ruptura e reposicao",
        "description": (
            "Priorize cobertura, risco de perda de venda, transferencia CD->loja, "
            "balanceamento entre lojas e acao com prazo."
        ),
        "checks": [
            "Identifique cobertura em dias, vendas recentes e estoque atual.",
            "Diferencie ruptura atual, alto risco e excesso.",
            "Quando houver desequilibrio entre lojas, recomende transferencia objetiva.",
        ],
    },
    {
        "title": "Promocao, margem e politica comercial",
        "description": (
            "Avalie promocao com disciplina de margem, volume incremental necessario, "
            "canibalizacao e risco de erosao de rentabilidade."
        ),
        "checks": [
            "Para desconto, bundle, leve x pague y ou liquidacao, use calculo deterministico.",
            "Separe receita, margem bruta, margem real e break-even de volume.",
            "Se faltar custo, frete, imposto ou mix, assuma menos e pergunte mais.",
        ],
    },
    {
        "title": "Cesta, cross-sell e afinidade de compra",
        "description": (
            "Use cestas para descobrir combinacoes, alavancar ticket medio e orientar "
            "campanhas ou exposicao em loja."
        ),
        "checks": [
            "Destaque itens que saem juntos com impacto comercial claro.",
            "Prefira recomendacoes acionaveis por categoria, loja ou campanha.",
            "Nao trate afinidade como causalidade sem evidencia.",
        ],
    },
    {
        "title": "Sazonalidade e planejamento de demanda",
        "description": (
            "Considere volta as aulas, carnaval, festas, artesanato, decoracao e "
            "eventos promocionais na leitura do negocio."
        ),
        "checks": [
            "Se houver contexto sazonal, ajuste abastecimento e timing promocional.",
            "Explique risco de antecipacao tardia ou excesso pos-pico.",
            "Quando a serie estiver fraca, sinalize baixa confianca explicitamente.",
        ],
    },
    {
        "title": "Pesquisa de mercado e concorrencia",
        "description": (
            "Use referencias externas para benchmark de preco e sortimento, mas "
            "deixe claro que sao sensiveis a data, praca e canal."
        ),
        "checks": [
            "Diferencie dado interno de referencia externa.",
            "Compare faixa de preco, dispersao e posicionamento relativo.",
            "Nao trate mercado aberto como verdade unica para decisao final.",
        ],
    },
]


MODE_HINTS: Dict[str, str] = {
    "default": "",
    "visual": (
        "MODO VISUAL: se houver grafico, complemente o que ele mostra com leitura "
        "executiva, outliers, gaps e recomendacoes. Nao repita o obvio."
    ),
    "seasonal": (
        "MODO SAZONAL: priorize risco de ruptura, antecipacao de compra, "
        "reposicao preventiva e janela de oportunidade comercial."
    ),
    "market": (
        "MODO MERCADO: trate pesquisa externa como benchmark, sempre destacando "
        "data, canal e concorrentes analisados."
    ),
    "calculation": (
        "MODO CALCULO: qualquer resposta sobre margem, desconto, preco, cesta, "
        "EOQ, previsao ou alocacao deve usar dados e ferramentas deterministicas."
    ),
}


def build_domain_playbooks() -> str:
    blocks: List[str] = []
    for playbook in DOMAIN_PLAYBOOKS:
        checks = "\n".join(f"- {item}" for item in playbook["checks"])
        blocks.append(
            f"### {playbook['title']}\n"
            f"{playbook['description']}\n"
            f"{checks}"
        )
    return "\n\n".join(blocks)


def get_mode_hint(mode: str) -> str:
    normalized = str(mode or "default").strip().lower()
    return MODE_HINTS.get(normalized, MODE_HINTS["default"])


def _truncate(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _normalize_tool_name(tool_call: Any) -> str:
    if not isinstance(tool_call, dict):
        return ""
    if tool_call.get("tool"):
        return str(tool_call.get("tool")).strip()
    if tool_call.get("name"):
        return str(tool_call.get("name")).strip()
    function_block = tool_call.get("function")
    if isinstance(function_block, dict) and function_block.get("name"):
        return str(function_block.get("name")).strip()
    return ""


def _normalize_tool_args(tool_call: Any) -> Any:
    if not isinstance(tool_call, dict):
        return None
    if isinstance(tool_call.get("parameters"), dict):
        return tool_call.get("parameters")
    if isinstance(tool_call.get("args"), dict):
        return tool_call.get("args")
    function_block = tool_call.get("function")
    if isinstance(function_block, dict):
        arguments = function_block.get("arguments")
        if isinstance(arguments, dict):
            return arguments
    return None


def _format_tool_call(tool_call: Any) -> str:
    tool_name = _normalize_tool_name(tool_call)
    if not tool_name:
        return ""
    args = _normalize_tool_args(tool_call)
    if not args:
        return tool_name
    payload = _truncate(json.dumps(args, ensure_ascii=False, sort_keys=True), 220)
    return f"{tool_name} {payload}"


def _score_example(example: Dict[str, Any], mode: str) -> int:
    category = str(example.get("category") or "").lower()
    user = str(example.get("user") or "").lower()
    response = str(example.get("assistant_response") or "")
    mode_hint = get_mode_hint(mode).lower()

    score = 0
    if example.get("tool_calls"):
        score += 4
    if response:
        score += min(3, max(1, len(response) // 180))

    high_value_keywords = [
        "ruptura",
        "margem",
        "promoc",
        "cesta",
        "mercado",
        "concorr",
        "sazon",
        "demanda",
        "loja",
        "segment",
    ]
    for keyword in high_value_keywords:
        if keyword in category or keyword in user:
            score += 2
    if mode_hint:
        for token in ("visual", "mercado", "calculo", "sazonal"):
            if token in mode_hint and (token in category or token in user):
                score += 2
    return score


def select_few_shot_examples(
    examples: Iterable[Dict[str, Any]],
    *,
    mode: str = "default",
    limit: int = 4,
) -> List[Dict[str, Any]]:
    ranked = sorted(
        (example for example in examples if isinstance(example, dict)),
        key=lambda item: (
            -_score_example(item, mode),
            str(item.get("category") or ""),
            str(item.get("user") or ""),
        ),
    )

    selected: List[Dict[str, Any]] = []
    used_categories: set[str] = set()

    for item in ranked:
        category = str(item.get("category") or "general").strip().lower()
        if category and category in used_categories and len(ranked) > limit:
            continue
        selected.append(item)
        used_categories.add(category)
        if len(selected) >= limit:
            return selected

    return ranked[:limit]


def format_few_shot_examples(examples: Iterable[Dict[str, Any]]) -> str:
    blocks: List[str] = []
    for index, example in enumerate(examples, start=1):
        tool_lines = [
            _format_tool_call(tool_call)
            for tool_call in (example.get("tool_calls") or [])
        ]
        tool_lines = [line for line in tool_lines if line]
        tools_text = "\n".join(f"- {line}" for line in tool_lines) if tool_lines else "- responder sem ferramenta"
        response_text = _truncate(str(example.get("assistant_response") or ""), 420)
        blocks.append(
            f"### Exemplo {index}\n"
            f"Pergunta: {_truncate(str(example.get('user') or ''), 220)}\n"
            f"Ferramentas esperadas:\n{tools_text}\n"
            f"Saida alvo:\n{response_text}"
        )
    return "\n\n".join(blocks)
