import re
from playwright.sync_api import Page, expect

def test_chat_load_and_greeting(page: Page):
    """
    Testa se o chat carrega e exibe a saudação inicial.
    """
    page.goto("http://localhost:3000") # Assumes frontend is running
    
    # Check if title is correct
    expect(page).to_have_title(re.compile("Agente BI"))
    
    # Check if chat input is visible
    expect(page.locator("textarea[placeholder*='Digite sua pergunta']")).to_be_visible()

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
