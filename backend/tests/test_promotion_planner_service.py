from backend.app.services.promotion_planner_service import PromotionPlannerService


def test_promotion_planner_detects_operational_promotion_query() -> None:
    query = "Como fazer uma promoção do EVA nas lojas 1685 e 2365 por 7 dias?"
    assert PromotionPlannerService.should_plan(query) is True


def test_promotion_planner_builds_operational_plan_with_real_data() -> None:
    service = PromotionPlannerService()
    response = service.build_plan(
        "Como fazer uma promoção do EVA nas lojas 1685 e 2365 por 7 dias?"
    )

    assert response["source"] == "service.promotion_planner"
    assert response["mode"] == "promotion_planner"
    message = response["result"]["mensagem"]
    assert "## Plano promocional" in message
    assert "## Como executar" in message
    assert "## KPI e gatilhos" in message
    assert isinstance(response.get("table_data"), list)
    assert response["table_data"]
