"""
Metadados canônicos de ferramentas para melhorar seleção de tool calling.
"""

from __future__ import annotations

from typing import Dict, List, Optional


TOOL_METADATA: Dict[str, Dict[str, object]] = {
    "consultar_dados_flexivel": {
        "summary": "Consulta dados internos de vendas, estoque, preço e ruptura no parquet corporativo.",
        "when_to_use": [
            "Perguntas sobre dados internos da Caçula com filtros por loja, produto, segmento ou período",
            "Listagens, somatórios, médias, rankings e recortes operacionais",
        ],
        "avoid_when": [
            "Busca vaga de produto por descrição imprecisa ou sinônimo",
            "Pesquisa externa de mercado ou concorrência",
        ],
        "critical_params": ["filtros", "colunas", "agregacao", "agrupar_por", "limite"],
        "examples": [
            "filtros={'UNE': 1685, 'NOMESEGMENTO': 'PAPELARIA'}",
            "agregacao='SUM' com coluna_agregacao='VENDA_30DD'",
        ],
    },
    "gerar_grafico_universal_v2": {
        "summary": "Gera gráfico operacional a partir de dados internos já filtrados por contexto de negócio.",
        "when_to_use": [
            "Usuário pede gráfico, ranking, tendência, painel ou visualização explícita",
            "Comparações por loja, categoria, segmento ou período",
        ],
        "avoid_when": [
            "Resposta puramente textual ou recomendação sem necessidade visual",
            "Quando faltarem dados mínimos para compor uma visualização confiável",
        ],
        "critical_params": ["descricao", "tipo_grafico", "filtro_une", "limite"],
    },
    "analisar_produto_todas_lojas": {
        "summary": "Analisa um produto específico em todas as lojas para estoque, venda, cobertura e gaps.",
        "when_to_use": [
            "Perguntas sobre SKU específico em múltiplas lojas",
            "Diagnóstico de ruptura, cobertura e priorização de transferência por produto",
        ],
        "avoid_when": [
            "Busca vaga por descrição sem código ou nome resolvido",
        ],
        "critical_params": ["produto_codigo"],
    },
    "encontrar_rupturas_criticas": {
        "summary": "Lista rupturas críticas com foco operacional em priorização de reposição e transferência.",
        "when_to_use": [
            "Perguntas sobre falta de estoque, itens zerados e urgência operacional",
        ],
        "avoid_when": [
            "Consultas gerais de estoque sem foco em ruptura",
        ],
        "critical_params": ["limite"],
    },
    "calcular_eoq": {
        "summary": "Calcula lote econômico de compra usando parâmetros reais de demanda, custo e armazenagem.",
        "when_to_use": [
            "Perguntas de ressuprimento, lote ideal, compra ótima e política de reposição",
        ],
        "avoid_when": [
            "Se não houver parâmetros de demanda/custo mínimos ou se a pergunta for apenas descritiva",
        ],
        "critical_params": [
            "demanda_anual",
            "custo_pedido",
            "custo_armazenagem_unitario",
        ],
    },
    "analisar_cesta_compras": {
        "summary": "Analisa cesta de compras e combinação de itens com margem, desconto e mix comercial.",
        "when_to_use": [
            "Perguntas sobre composição de carrinho, cross-sell e rentabilidade da cesta",
        ],
        "avoid_when": [
            "Quando a pergunta é sobre um único produto sem contexto de conjunto",
        ],
        "critical_params": ["itens"],
    },
    "simular_promocao_cesta": {
        "summary": "Simula promoção real sobre cesta ou itens considerando desconto, margem e impacto econômico.",
        "when_to_use": [
            "Avaliação de desconto, campanha, combo ou promoção com impacto em margem",
        ],
        "avoid_when": [
            "Quando faltarem preços, custos ou estrutura mínima dos itens",
        ],
        "critical_params": ["itens", "desconto_pct", "meta_margem_pct"],
    },
    "pesquisar_precos_concorrentes": {
        "summary": "Pesquisa preços de concorrentes específicos da Caçula em fontes externas controladas.",
        "when_to_use": [
            "Benchmark concorrencial com player conhecido e foco em preço comparado",
        ],
        "avoid_when": [
            "Consultas de dados internos ou perguntas amplas de mercado sem concorrente definido",
        ],
        "critical_params": ["produto", "concorrentes", "estado"],
    },
    "pesquisar_mercado_web": {
        "summary": "Pesquisa referências abertas de mercado para produto/categoria quando não há concorrente único definido.",
        "when_to_use": [
            "Benchmark aberto, sinais de mercado, Google Shopping, marketplace e tendências externas",
        ],
        "avoid_when": [
            "Consulta interna de BI ou comparação com concorrente específico da Caçula",
        ],
        "critical_params": ["query", "categoria", "estado"],
    },
    "buscar_produtos_inteligente": {
        "summary": "Resolve busca vaga de produto por descrição, sinônimo, typo ou nome incompleto usando retrieval híbrido.",
        "when_to_use": [
            "Usuário descreve o produto de forma imprecisa",
            "A busca exata por código ou nome falha",
        ],
        "avoid_when": [
            "Pergunta já tem código exato do produto",
        ],
        "critical_params": ["descricao", "limite", "usar_hybrid"],
    },
}


def compose_tool_description(tool_name: str, fallback_description: str = "") -> str:
    metadata = TOOL_METADATA.get(tool_name)
    if not metadata:
        return (fallback_description or "").strip()

    lines: List[str] = [str(metadata.get("summary") or fallback_description or "").strip()]

    when_to_use = metadata.get("when_to_use") or []
    if when_to_use:
        lines.append("USE QUANDO: " + "; ".join(str(item) for item in when_to_use))

    avoid_when = metadata.get("avoid_when") or []
    if avoid_when:
        lines.append("NAO USE QUANDO: " + "; ".join(str(item) for item in avoid_when))

    critical_params = metadata.get("critical_params") or []
    if critical_params:
        lines.append("PARAMETROS CRITICOS: " + ", ".join(str(item) for item in critical_params))

    examples = metadata.get("examples") or []
    if examples:
        lines.append("EXEMPLOS: " + " | ".join(str(item) for item in examples))

    return "\n".join(line for line in lines if line)


def get_tool_metadata(tool_name: str) -> Optional[Dict[str, object]]:
    return TOOL_METADATA.get(tool_name)
