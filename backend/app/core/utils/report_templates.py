from __future__ import annotations

from typing import Any, Dict, List


_OFFICIAL_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "compras_cotacao",
        "processo": "compras",
        "nome": "Cotacao e Negociacao",
        "descricao": "Comparacao de faixa de preco com recomendacao de negociacao.",
        "keywords": ["cotacao", "cotação", "preco", "preço", "concorrente", "fornecedor", "mercado"],
    },
    {
        "id": "compras_ruptura",
        "processo": "compras",
        "nome": "Ruptura Critica",
        "descricao": "Priorizacao de itens sem estoque e plano de reposicao.",
        "keywords": ["ruptura", "sem estoque", "reposicao", "reposição", "abastecimento"],
    },
    {
        "id": "compras_eoq",
        "processo": "compras",
        "nome": "Lote Economico (EOQ)",
        "descricao": "Sugestao de lote com equilibrio entre custo e cobertura.",
        "keywords": ["eoq", "lote", "quanto comprar", "pedido", "compra"],
    },
    {
        "id": "comercial_vendas",
        "processo": "comercial",
        "nome": "Performance de Vendas",
        "descricao": "Leitura de vendas por loja/segmento com foco em acao comercial.",
        "keywords": ["venda", "faturamento", "receita", "ticket", "segmento", "une", "loja"],
    },
    {
        "id": "comercial_margem",
        "processo": "comercial",
        "nome": "Margem e Preco",
        "descricao": "Recomendacao de precificacao e mix orientada a margem.",
        "keywords": ["margem", "preco", "preço", "desconto", "markup", "mix"],
    },
    {
        "id": "comercial_transferencia",
        "processo": "comercial",
        "nome": "Transferencia e Balanceamento",
        "descricao": "Realocacao entre lojas para reduzir ruptura e excesso.",
        "keywords": ["transferencia", "transferência", "alocar", "redistribuir", "estoque parado"],
    },
]


def get_official_report_templates() -> List[Dict[str, Any]]:
    """
    Retorna catalogo oficial de templates ChatBI (Fase 3).
    """
    return [dict(item) for item in _OFFICIAL_TEMPLATES]


def select_official_report_template(query: str) -> Dict[str, Any]:
    """
    Seleciona template oficial por heuristica de keywords.
    """
    q = (query or "").lower()
    best_score = -1
    best_template = None

    for template in _OFFICIAL_TEMPLATES:
        score = 0
        for keyword in template.get("keywords", []):
            if keyword in q:
                score += 1
        if score > best_score:
            best_score = score
            best_template = template

    if best_template and best_score > 0:
        return dict(best_template)

    return {
        "id": "geral_executivo",
        "processo": "geral",
        "nome": "Executivo Padrao",
        "descricao": "Resposta executiva padronizada para decisoes de negocio.",
        "keywords": [],
    }
