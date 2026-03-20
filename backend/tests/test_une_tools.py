import pandas as pd

from backend.app.core.tools import une_tools


def test_analisar_produto_todas_lojas_uses_extended_limit(monkeypatch):
    captured = {}

    def fake_load_data(filters=None, columns=None, limit=100):
        captured["filters"] = filters
        captured["limit"] = limit
        return pd.DataFrame(
            [
                {
                    "nome_produto": "CANETA BIC",
                    "estoque_atual": 10,
                    "venda_30_d": 20,
                    "une": 1685,
                    "une_nome": "261",
                    "estoque_cd": 100,
                    "linha_verde": 15,
                },
                {
                    "nome_produto": "CANETA BIC",
                    "estoque_atual": 0,
                    "venda_30_d": 8,
                    "une": 2599,
                    "une_nome": "ITA",
                    "estoque_cd": 100,
                    "linha_verde": 10,
                },
            ]
        )

    monkeypatch.setattr(une_tools, "_load_data", fake_load_data)

    result = une_tools.analisar_produto_todas_lojas.invoke({"produto_codigo": 25})

    assert captured["filters"] == {"codigo": 25}
    assert captured["limit"] == 10000
    assert result["success"] is True
    assert result["resumo"]["total_lojas_com_produto"] == 2
