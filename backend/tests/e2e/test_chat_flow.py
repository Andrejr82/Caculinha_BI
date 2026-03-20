import re
import os
import importlib.util

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.manual]

if os.getenv("RUN_E2E_TESTS", "0") != "1":
    pytest.skip(
        "teste E2E manual; defina RUN_E2E_TESTS=1 para executar.",
        allow_module_level=True,
    )

if importlib.util.find_spec("pytest_playwright") is None:
    pytest.skip(
        "pytest-playwright não instalado neste ambiente; use a suíte frontend-solid/tests/integration para o E2E real.",
        allow_module_level=True,
    )

pytest.importorskip("playwright.sync_api", reason="Playwright não instalado para E2E.")
from playwright.sync_api import Page, expect

def test_chat_load_and_greeting(page: Page):
    """
    Testa se o chat carrega e exibe a saudação inicial.
    """
    page.goto("http://localhost:3000") # Assumes frontend is running
    
    # Check if title is correct
    expect(page).to_have_title(re.compile("Agente BI"))
    
    # Check if chat input is visible
    expect(page.locator("textarea[placeholder*='Enviar mensagem para o Caçulinha']")).to_be_visible()

def test_send_message_and_receive_response(page: Page):
    """
    Testa o envio de uma mensagem e o recebimento de uma resposta (streaming).
    """
    page.goto("http://localhost:3000")
    
    # Type message
    page.fill("textarea", "Qual o total de vendas?")
    page.click("button[type='submit']")
    
    # Check if user message appears
    expect(page.locator("text=Qual o total de vendas?")).to_be_visible()
    
    # Check if loading/streaming indicator appears (optional)
    # expect(page.locator(".typing-indicator")).to_be_visible()
    
    # Wait for response (timeout 30s)
    # We look for something that resembles a number or "Total de Vendas"
    expect(page.locator("text=Total de Vendas")).to_be_visible(timeout=30000)

def test_chart_rendering(page: Page):
    """
    Testa se o gráfico é renderizado quando solicitado.
    """
    page.goto("http://localhost:3000")
    
    page.fill("textarea", "Gere um gráfico de vendas por categoria")
    page.click("button[type='submit']")
    
    # Wait for chart container
    expect(page.locator(".plotly-graph-div")).to_be_visible(timeout=30000)


def test_contextual_followup_generates_action_plan_instead_of_raw_dump(page: Page):
    """
    Caso real de regressão:
    1. usuário pede gráfico por segmento em toda a rede
    2. usuário pede plano comercial para UNEs de menor venda
    O chat deve manter contexto e devolver plano acionável, não tabela bruta de SKUs.
    """
    page.goto("http://localhost:3000")

    page.fill("textarea", "gere um gráfico de vendas de todos os segmentos em todas as unes")
    page.click("button[type='submit']")
    expect(page.locator(".plotly-graph-div")).to_be_visible(timeout=30000)
    expect(page.locator("text=Segmento")).to_be_visible(timeout=30000)

    page.fill("textarea", "me de um plano comercial de 7 dias para as unes de menor venda")
    page.click("button[type='submit']")

    expect(page.locator("text=Plano comercial de 7 dias")).to_be_visible(timeout=30000)
    expect(page.locator("text=Dia 1")).to_be_visible(timeout=30000)
    expect(page.locator("text=Código do produto")).to_have_count(0)
