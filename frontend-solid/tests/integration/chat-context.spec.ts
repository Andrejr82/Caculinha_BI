import { test, expect } from './setup';

const expectRenderedChart = async (page: Parameters<typeof test>[0]['authenticatedPage']) => {
  await expect(page.locator('[data-testid="adaptive-chart-canvas"], svg.main-svg').first()).toBeVisible({ timeout: 60000 });
};

test.describe('Chat Context Continuity', () => {
  test('keeps context from chart request into 7-day commercial plan follow-up', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    await page.evaluate(() => localStorage.removeItem('chat_session_id'));
    await page.reload();
    await page.waitForLoadState('networkidle');

    const input = page.locator('textarea').first();
    await expect(input).toBeVisible({ timeout: 30000 });

    await input.fill('gere um gráfico de vendas de todos os segmentos em todas as unes');
    await page.keyboard.press('Enter');

    await expectRenderedChart(page);
    await expect(page.locator('body')).toContainText('Segmento', { timeout: 60000 });

    await input.fill('me de um plano comercial de 7 dias para as unes de menor venda');
    await page.keyboard.press('Enter');

    await expect(page.locator('body')).toContainText('Plano comercial de 7 dias', { timeout: 60000 });
    await expect(page.locator('body')).toContainText('Dia 1', { timeout: 60000 });
    await expect(page.locator('body')).not.toContainText('Código do produto');
  });

  test('turns a generic strategic follow-up into an actionable plan using the previous answer context', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    await page.evaluate(() => localStorage.removeItem('chat_session_id'));
    await page.reload();
    await page.waitForLoadState('networkidle');

    const input = page.locator('textarea').first();
    await expect(input).toBeVisible({ timeout: 30000 });

    await input.fill('gere um gráfico de vendas de todos os segmentos em todas as unes');
    await page.keyboard.press('Enter');

    await expectRenderedChart(page);
    await expect(page.locator('body')).toContainText('Segmento', { timeout: 60000 });

    await input.fill('com base na última resposta, quais ações você recomenda?');
    await page.keyboard.press('Enter');

    await expect(page.locator('body')).toContainText('Plano comercial de 7 dias', { timeout: 60000 });
    await expect(page.locator('body')).toContainText('Próximas ações', { timeout: 60000 });
  });

  test('turns a dashboard follow-up into a critical-points analysis instead of repeating the dashboard stub', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    await page.evaluate(() => localStorage.removeItem('chat_session_id'));
    await page.reload();
    await page.waitForLoadState('networkidle');

    const input = page.locator('textarea').first();
    await expect(input).toBeVisible({ timeout: 30000 });

    await input.fill('gere um dashboard interativo do segmento ARTES nos últimos 30 dias com tabela por UNE');
    await page.keyboard.press('Enter');

    await expect(page.locator('body')).toContainText('Painel de Vendas', { timeout: 60000 });
    await expect(page.locator('body')).toContainText('segmento: ARTES', { timeout: 60000 });
    await expectRenderedChart(page);

    await input.fill('com base nesse dashboard, detalhe os pontos críticos');
    await page.keyboard.press('Enter');

    const latestAssistantText = page.locator('.markdown-body').last();
    await expect(latestAssistantText).toContainText('Próximas ações', { timeout: 60000 });
    await expect(latestAssistantText).toContainText('base do ranking', { timeout: 60000 });
    await expect(latestAssistantText).not.toContainText('Dashboard interativo gerado com sucesso');
  });

  test('turns a market research follow-up into a negotiation recommendation using the previous response', async ({ authenticatedPage: page }) => {
    test.setTimeout(180000);

    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    await page.evaluate(() => localStorage.removeItem('chat_session_id'));
    await page.reload();
    await page.waitForLoadState('networkidle');

    const input = page.locator('textarea').first();
    await expect(input).toBeVisible({ timeout: 30000 });

    await input.fill('faça uma pesquisa de mercado do produto lapis de cor 12 cores');
    await page.keyboard.press('Enter');

    const firstResearchMessage = page.locator('.markdown-body').last();
    await expect(firstResearchMessage).toContainText(/Pesquisa (concorrencial|de mercado) conclu/i, { timeout: 120000 });

    await input.fill('com base nessa pesquisa, o que você recomenda para negociação?');
    await page.keyboard.press('Enter');

    const latestAssistantText = page.locator('.markdown-body').last();
    await expect(latestAssistantText).toContainText('Recomendação de negociação', { timeout: 60000 });
    await expect(latestAssistantText).not.toContainText('tempo limite de processamento', { timeout: 60000 });
  });

  test('reuses the previous market-research product when the user asks for a specific competitor only', async ({ authenticatedPage: page }) => {
    test.setTimeout(180000);

    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    await page.evaluate(() => localStorage.removeItem('chat_session_id'));
    await page.reload();
    await page.waitForLoadState('networkidle');

    const input = page.locator('textarea').first();
    await expect(input).toBeVisible({ timeout: 30000 });

    await input.fill('faça uma pesquisa de mercado do produto lapis de cor 12 cores');
    await page.keyboard.press('Enter');

    const firstResearchMessage = page.locator('.markdown-body').last();
    await expect(firstResearchMessage).toContainText(/Pesquisa (concorrencial|de mercado) conclu/i, { timeout: 120000 });

    await input.fill('e na Kalunga?');
    await page.keyboard.press('Enter');

    const latestAssistantText = page.locator('.markdown-body').last();
    await expect(latestAssistantText).toContainText('Kalunga', { timeout: 120000 });
    await expect(latestAssistantText).not.toContainText('tempo limite de processamento', { timeout: 120000 });
  });
});
