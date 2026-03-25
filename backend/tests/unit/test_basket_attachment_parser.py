from backend.app.core.tools.basket_attachment_parser import (
    build_basket_payload_from_documents,
    parse_single_attachment,
)


def test_parse_single_attachment_csv_items_table() -> None:
    content = """sku,nome,quantidade,preco_unitario,custo_unitario,imposto_pct,frete_valor
CAN-001,Caneta Azul,10,4.90,2.10,8,4
CAD-001,Caderno,5,19.90,12.00,8,6
"""

    parsed = parse_single_attachment(content, filename="cesta.csv")

    assert parsed is not None
    assert parsed["kind"] == "itens"
    assert len(parsed["payload"]["itens"]) == 2
    assert parsed["payload"]["itens"][0]["sku"] == "CAN-001"


def test_parse_single_attachment_csv_transactions_table() -> None:
    content = """pedido,produto
1001,fralda
1001,cerveja
1002,fralda
1002,lenco
"""

    parsed = parse_single_attachment(content, filename="transacoes.csv")

    assert parsed is not None
    assert parsed["kind"] == "transacoes"
    assert ["cerveja", "fralda"] in parsed["payload"]["transacoes"]


def test_parse_single_attachment_prefers_transactions_when_transaction_id_is_explicit() -> None:
    content = """transaction_id,produto,valor_unitario
500001,ZIPER,9.99
500001,FITA CETIM,49.90
500002,CADERNO,12.90
500002,CANETA,12.90
"""

    parsed = parse_single_attachment(content, filename="basket_realista.csv")

    assert parsed is not None
    assert parsed["kind"] == "transacoes"
    assert ["FITA CETIM", "ZIPER"] in parsed["payload"]["transacoes"]
    assert ["CADERNO", "CANETA"] in parsed["payload"]["transacoes"]


def test_build_basket_payload_from_documents_groups_document_chunks() -> None:
    documents = [
        {
            "document_id": "doc-1",
            "content": "pedido,produto\n1001,fralda\n1001,cerveja\n",
            "metadata": {"filename": "mercado.csv"},
        },
        {
            "document_id": "doc-1",
            "content": "1002,fralda\n1002,lenco\n",
            "metadata": {"filename": "mercado.csv"},
        },
    ]

    parsed = build_basket_payload_from_documents(documents, preferred_kind="transacoes")

    assert parsed is not None
    assert parsed["kind"] == "transacoes"
    assert len(parsed["payload"]["transacoes"]) == 2
    assert parsed["files"] == ["mercado.csv"]
