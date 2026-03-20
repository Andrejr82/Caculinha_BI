from backend.app.core.tools.basket_tools import (
    analyze_basket_logic,
    mine_market_basket_logic,
    simulate_promotion_logic,
)


def test_analyze_basket_logic_calculates_real_margin_deterministically() -> None:
    result = analyze_basket_logic(
        [
            {
                "sku": "A",
                "nome": "Item A",
                "quantidade": 2,
                "preco_unitario": 100,
                "custo_unitario": 60,
                "desconto_pct": 10,
                "imposto_pct": 5,
                "frete_valor": 10,
                "despesa_variavel_pct": 2,
            },
            {
                "sku": "B",
                "nome": "Item B",
                "quantidade": 1,
                "preco_unitario": 50,
                "custo_unitario": 20,
                "imposto_pct": 5,
                "despesa_variavel_pct": 2,
            },
        ]
    )

    assert result["totais"]["receita_liquida"] == 230.0
    assert result["totais"]["margem_real_valor"] == 63.9
    assert result["totais"]["margem_real_pct"] == 27.78
    assert result["totais"]["margem_bruta_pct"] == 39.13


def test_simulate_promotion_logic_reports_break_even_uplift() -> None:
    result = simulate_promotion_logic(
        itens=[
            {
                "sku": "A",
                "nome": "Item A",
                "quantidade": 2,
                "preco_unitario": 100,
                "custo_unitario": 60,
            }
        ],
        tipo_promocao="percentual",
        desconto_pct=10,
    )

    assert result["antes"]["margem_real_valor"] == 80.0
    assert result["depois"]["margem_real_valor"] == 60.0
    assert result["uplift_necessario_para_empatar_pct"] == 33.33


def test_market_basket_logic_finds_association_with_or_without_mlxtend() -> None:
    result = mine_market_basket_logic(
        transacoes=[
            ["fralda", "cerveja"],
            ["fralda", "cerveja"],
            ["fralda", "cerveja"],
            ["pao"],
        ],
        suporte_minimo=0.5,
        confianca_minima=0.5,
        lift_minimo=1.0,
        max_resultados=10,
    )

    assert result["total_transacoes"] == 4
    assert any(
        set(rule["antecedente"]) == {"fralda"} and set(rule["consequente"]) == {"cerveja"}
        for rule in result["regras_associacao"]
    )
