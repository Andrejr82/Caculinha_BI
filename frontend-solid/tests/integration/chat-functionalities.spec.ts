import { test, expect } from './setup';

async function openFreshChat(page: Parameters<typeof test>[0]['authenticatedPage']) {
  await page.goto('/chat');
  await page.waitForLoadState('networkidle');

  await page.evaluate(() => localStorage.removeItem('chat_session_id'));
  await page.reload();
  await page.waitForLoadState('networkidle');

  const input = page.locator('textarea').first();
  await expect(input).toBeVisible({ timeout: 30000 });
  return input;
}

const expectRenderedChart = async (page: Parameters<typeof test>[0]['authenticatedPage']) => {
  await expect(page.locator('[data-testid="adaptive-chart-canvas"], svg.main-svg').first()).toBeVisible({ timeout: 60000 });
};

test.describe('Chat Functionalities', () => {
  test('renders a table answer in browser real', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    const input = await openFreshChat(page);

    await input.fill('me mostre em tabela as vendas por loja do segmento tecidos nos ultimos 30 dias');
    await page.keyboard.press('Enter');

    const renderedTable = page.locator('table').last();
    await expect(renderedTable).toBeVisible({ timeout: 60000 });
    await expect(page.locator('body')).toContainText(/ranking|loja|une|participacao|part\\.? %/i, { timeout: 60000 });
  });

  test('renders a dashboard answer in browser real', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    const input = await openFreshChat(page);

    await input.fill('gere um dashboard interativo do segmento artes nos ultimos 30 dias com tabela por UNE');
    await page.keyboard.press('Enter');

    await expect(page.locator('body')).toContainText('Painel de Vendas', { timeout: 60000 });
    await expectRenderedChart(page);
    await expect(page.locator('table').last()).toBeVisible({ timeout: 60000 });
  });

  test('renders an analytical sales report in chat without automation card', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    const input = await openFreshChat(page);

    await input.fill('preciso de um relatório de vendas do segmento tecidos de todas as lojas');
    await page.keyboard.press('Enter');

    const latestAssistantText = page.locator('.markdown-body').last();
    const renderedTable = page.locator('table').last();

    await expect(latestAssistantText).toContainText('Resumo executivo', { timeout: 60000 });
    await expect(latestAssistantText).toContainText('Tabela operacional', { timeout: 60000 });
    await expect(latestAssistantText).toContainText('Próximas ações', { timeout: 60000 });
    await expect(renderedTable).toBeVisible({ timeout: 60000 });
    await expect(page.locator('body')).not.toContainText('Automação assistida', { timeout: 60000 });
    await expect(page.locator('body')).not.toContainText(
      'Posso preparar automações assistidas, mas esse recurso não está habilitado para o seu perfil no momento.',
      { timeout: 60000 },
    );
  });

  test('exports the conversation as JSON', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    const input = await openFreshChat(page);

    await input.fill('gere um grafico de vendas de todos os segmentos em todas as unes');
    await page.keyboard.press('Enter');

    await expectRenderedChart(page);

    await page.getByRole('button', { name: /exportar/i }).click();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'JSON' }).click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/^chatbi-.*\.json$/i);
  });

  test('uploads an attachment and keeps the chat flow usable', async ({ authenticatedPage: page }) => {
    test.setTimeout(180000);

    const input = await openFreshChat(page);
    const fileInput = page.locator('input[type="file"]').first();

    await fileInput.setInputFiles({
      name: 'resumo_lojas.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from('loja,venda\n1685,311492.84\n520,154720.52\n35,131685.89\n', 'utf-8'),
    });

    await expect(page.locator('body')).toContainText('resumo_lojas.csv', { timeout: 10000 });

    await input.fill('com base no arquivo anexado, resuma os principais pontos');
    await page.keyboard.press('Enter');

    await expect(page.locator('body')).toContainText('Anexos enviados:', { timeout: 30000 });
    await expect(page.locator('body')).not.toContainText('Nao foi possivel enviar os anexos agora', { timeout: 60000 });
    await expect(page.locator('.markdown-body').last()).toBeVisible({ timeout: 90000 });
  });
});
