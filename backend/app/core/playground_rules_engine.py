from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path


CATALOG_PATH = Path(__file__).resolve().parent / "prompts" / "bi_intents_catalog.json"


@dataclass(frozen=True)
class PlaygroundRuleResult:
    matched: bool
    response: str
    source: str
    confidence: float
    intent: str


def load_bi_intents_catalog() -> dict:
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": "unknown", "domain": "playground_bi", "intents": []}


def build_structured_response(
    *,
    json_mode: bool,
    summary: str,
    table_headers: list[str],
    table_rows: list[list[str]],
    action: str,
    template: str | None = None,
    language: str | None = None,
    dialect: str | None = None,
) -> str:
    if json_mode:
        payload: dict = {
            "summary": summary,
            "table": {"headers": table_headers, "rows": table_rows},
            "action": action,
        }
        if template:
            payload["template"] = template
        if language:
            payload["language"] = language
        if dialect:
            payload["dialect"] = dialect
        if template and language == "sql":
            payload["query"] = template
        if template and language == "python":
            payload["code"] = template
        return json.dumps(payload, ensure_ascii=False, indent=2)

    table_md = ""
    if table_headers:
        header = "| " + " | ".join(table_headers) + " |"
        divider = "| " + " | ".join(["---"] * len(table_headers)) + " |"
        lines = [header, divider]
        for row in table_rows:
            lines.append("| " + " | ".join(row) + " |")
        table_md = "\n".join(lines)

    parts = [
        "## Resumo",
        summary,
        "",
        "## Tabela",
        table_md if table_md else "_Sem dados tabulares para este caso._",
        "",
        "## Ação recomendada",
        action,
    ]
    if template and language:
        parts.extend(["", "## Template sugerido", f"```{language}", template, "```"])
    return "\n".join(parts)


def _python_parquet_status_error(json_mode: bool) -> str:
    code = (
        "import polars as pl\n\n"
        "df = pl.read_parquet('dados.parquet')\n"
        "resultado = df.filter(pl.col('status') == 'error')\n"
        "print(resultado)\n"
    )
    return build_structured_response(
        json_mode=json_mode,
        summary="Gerar script para leitura de Parquet e filtro por status de erro.",
        table_headers=["Etapa", "Descrição"],
        table_rows=[
            ["Leitura", "Carrega arquivo Parquet com Polars"],
            ["Filtro", "Mantém apenas linhas com status = error"],
            ["Saída", "Imprime dataframe filtrado"],
        ],
        action="Executar o script com o caminho real do arquivo e validar volume de erros por período.",
        template=code,
        language="python",
    )


def _sql_products_no_sales_last_6_months(json_mode: bool) -> str:
    sql = (
        "SELECT p.id_produto, p.nome_produto\n"
        "FROM produtos p\n"
        "LEFT JOIN vendas v\n"
        "  ON v.id_produto = p.id_produto\n"
        " AND v.data_venda >= DATEADD(MONTH, -6, GETDATE())\n"
        "WHERE v.id_produto IS NULL;\n"
    )
    return build_structured_response(
        json_mode=json_mode,
        summary="Identificar produtos sem vendas nos últimos 6 meses para ação comercial/estoque.",
        table_headers=["Campo", "Finalidade"],
        table_rows=[
            ["id_produto", "Chave para análise operacional"],
            ["nome_produto", "Identificação legível para o time BI"],
        ],
        action="Priorizar revisão de sortimento e ativação promocional para itens sem giro.",
        template=sql,
        language="sql",
        dialect="sqlserver",
    )


def _sql_ruptura_by_store_period(json_mode: bool) -> str:
    sql = (
        "SELECT loja, produto_id, produto_nome, estoque_atual, estoque_minimo, data_referencia\n"
        "FROM rupturas\n"
        "WHERE loja = @loja\n"
        "  AND data_referencia BETWEEN @data_inicio AND @data_fim\n"
        "  AND estoque_atual <= estoque_minimo\n"
        "ORDER BY data_referencia DESC;\n"
    )
    return build_structured_response(
        json_mode=json_mode,
        summary="Mapear rupturas por loja e período com foco em itens abaixo do estoque mínimo.",
        table_headers=["Parâmetro", "Uso"],
        table_rows=[
            ["@loja", "Filtra unidade específica"],
            ["@data_inicio", "Início da janela de análise"],
            ["@data_fim", "Fim da janela de análise"],
        ],
        action="Rodar por loja crítica e priorizar reposição para produtos recorrentes em ruptura.",
        template=sql,
        language="sql",
        dialect="sqlserver",
    )


def _sql_transfer_suggestions(json_mode: bool) -> str:
    sql = (
        "WITH origem AS (\n"
        "  SELECT produto_id, loja AS loja_origem, estoque_atual\n"
        "  FROM estoque_loja\n"
        "  WHERE estoque_atual > estoque_minimo * 1.5\n"
        "),\n"
        "destino AS (\n"
        "  SELECT produto_id, loja AS loja_destino, estoque_atual, estoque_minimo\n"
        "  FROM estoque_loja\n"
        "  WHERE estoque_atual < estoque_minimo\n"
        ")\n"
        "SELECT d.produto_id, o.loja_origem, d.loja_destino,\n"
        "       CAST((d.estoque_minimo - d.estoque_atual) AS INT) AS qtd_sugerida\n"
        "FROM destino d\n"
        "JOIN origem o ON o.produto_id = d.produto_id\n"
        "WHERE o.loja_origem <> d.loja_destino\n"
        "ORDER BY qtd_sugerida DESC;\n"
    )
    return build_structured_response(
        json_mode=json_mode,
        summary="Gerar sugestões de transferência entre lojas com excesso e falta de estoque.",
        table_headers=["Coluna", "Significado"],
        table_rows=[
            ["loja_origem", "Unidade com potencial de envio"],
            ["loja_destino", "Unidade com falta de estoque"],
            ["qtd_sugerida", "Quantidade sugerida para reequilíbrio"],
        ],
        action="Validar custo logístico e aprovar apenas sugestões com alta criticidade no destino.",
        template=sql,
        language="sql",
        dialect="sqlserver",
    )


def _admat_une_operational_checklist(json_mode: bool) -> str:
    payload = {
        "processo": "ADMAT_UNE",
        "regras_chave": [
            "Disparar análise de abastecimento quando estoque <= 50% da média comum.",
            "Priorizar itens de linha verde e alto giro antes da carga de baixa criticidade.",
            "Respeitar múltiplos de compra/embalagem e arredondamento operacional.",
            "Validar promoções e sazonalidade antes de gerar pedido final.",
            "Gerar trilha de auditoria por item: regra aplicada, estoque base, sugestão final."
        ],
        "saida_esperada": {
            "campos": ["produto_id", "loja", "estoque_atual", "media_comum", "qtd_sugerida", "regra_disparo"],
            "acao": "revisao_analista"
        }
    }
    if json_mode:
        return json.dumps(payload, ensure_ascii=False, indent=2)

    return build_structured_response(
        json_mode=False,
        summary="Checklist operacional ADMAT/UNE para tomada de decisão de abastecimento.",
        table_headers=["Regra", "Objetivo"],
        table_rows=[
            ["<= 50% média comum", "Disparar análise de reposição"],
            ["Linha verde prioritária", "Maximizar disponibilidade de itens críticos"],
            ["Múltiplos e arredondamento", "Evitar pedidos fora de padrão logístico"],
        ],
        action="Executar revisão analítica antes da aprovação final de pedido e registrar trilha de auditoria.",
        template=None,
        language=None,
    )


def _sql_total_sales_all_unes(json_mode: bool) -> str:
    sql = (
        "SELECT\n"
        "  v.une,\n"
        "  SUM(v.valor_total) AS venda_total\n"
        "FROM vendas v\n"
        "GROUP BY v.une\n"
        "ORDER BY venda_total DESC;\n"
    )
    return build_structured_response(
        json_mode=json_mode,
        summary="Consolidar venda total por UNE para visão comparativa de performance.",
        table_headers=["Coluna", "Descrição"],
        table_rows=[
            ["une", "Identificador da unidade (UNE)"],
            ["venda_total", "Soma do valor total vendido por UNE"],
        ],
        action="Executar a query e usar o ranking para priorizar ações comerciais por unidade.",
        template=sql,
        language="sql",
        dialect="sqlserver",
    )


def resolve_playground_rule(message: str, json_mode: bool = False) -> Optional[PlaygroundRuleResult]:
    text = (message or "").lower()
    if not text.strip():
        return None

    if "parquet" in text and "status" in text and "error" in text:
        return PlaygroundRuleResult(
            matched=True,
            response=_python_parquet_status_error(json_mode=json_mode),
            source="rules-engine",
            confidence=0.98,
            intent="parquet.filter.status_error",
        )

    if "sql" in text and "produtos" in text and "6" in text and "mes" in text and ("não venderam" in text or "nao venderam" in text):
        return PlaygroundRuleResult(
            matched=True,
            response=_sql_products_no_sales_last_6_months(json_mode=json_mode),
            source="rules-engine",
            confidence=0.92,
            intent="sql.produtos_sem_venda_6_meses",
        )

    if "ruptura" in text and ("loja" in text or "periodo" in text or "período" in text):
        return PlaygroundRuleResult(
            matched=True,
            response=_sql_ruptura_by_store_period(json_mode=json_mode),
            source="rules-engine",
            confidence=0.93,
            intent="sql.ruptura_por_loja_periodo",
        )

    if "transfer" in text and ("loja" in text or "estoque" in text):
        return PlaygroundRuleResult(
            matched=True,
            response=_sql_transfer_suggestions(json_mode=json_mode),
            source="rules-engine",
            confidence=0.9,
            intent="sql.sugestao_transferencia_lojas",
        )

    if (
        ("query" in text or "sql" in text)
        and ("venda total" in text or ("venda" in text and "total" in text))
        and ("une" in text or "unes" in text or "loja" in text)
    ):
        return PlaygroundRuleResult(
            matched=True,
            response=_sql_total_sales_all_unes(json_mode=json_mode),
            source="rules-engine",
            confidence=0.96,
            intent="sql.venda_total_por_une",
        )

    if "admat" in text or "linha verde" in text or "media comum" in text or "média comum" in text:
        return PlaygroundRuleResult(
            matched=True,
            response=_admat_une_operational_checklist(json_mode=json_mode),
            source="rules-engine",
            confidence=0.88,
            intent="bi.admat_une_checklist",
        )

    return None
