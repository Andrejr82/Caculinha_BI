import { test, expect } from './setup';

test.describe('Stabilization Flows', () => {
  test('login -> Chat page -> message streams or degrades gracefully', async ({ authenticatedPage: page }) => {
    await page.goto('/chat');
    await page.waitForLoadState('networkidle');

    const input = page.locator('textarea, input[type="text"]').first();
    await expect(input).toBeVisible();
    await input.fill('teste de estabilizacao');
    await page.keyboard.press('Enter');

    await page.waitForTimeout(3000);
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(0);
    expect(bodyText.toLowerCase()).not.toContain('unhandled');
  });

  test('login -> CodeChat -> works or shows actionable index message', async ({ adminPage: page }) => {
    await page.goto('/code-chat');
    await page.waitForLoadState('networkidle');

    const input = page.locator('input[type="text"]').first();
    await expect(input).toBeVisible();
    await input.fill('listar módulos principais');
    await page.keyboard.press('Enter');

    await page.waitForTimeout(3000);
    const bodyText = (await page.locator('body').innerText()).toLowerCase();
    expect(
      bodyText.includes('index missing; run scripts/index_codebase.py') ||
      bodyText.includes('agente') ||
      bodyText.includes('referências de código')
    ).toBeTruthy();
  });

  test('login -> Playground -> streams or degrades fast on quota', async ({ adminPage: page }) => {
    await page.goto('/playground');
    await page.waitForLoadState('networkidle');

    const input = page.locator('textarea').first();
    await expect(input).toBeVisible();
    await input.fill('explique rapidamente as vendas');
    await page.keyboard.press('Enter');

    const assistantBubble = page.locator('.playground-message--assistant').last();
    await expect(assistantBubble).toBeVisible({ timeout: 10000 });
    await expect(assistantBubble).toContainText(
      /processando resposta|sem resposta retornada|falha de conexão|modo degradado|playground|resumo executivo/i,
    );
  });

  test('login -> Playground lab -> compare controls stay reachable', async ({ adminPage: page }) => {
    await page.goto('/playground-lab');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('button', { name: /single/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /compare/i })).toBeVisible();

    const input = page.getByLabel(/prompt principal do laboratório/i);
    await expect(input).toBeVisible();
    await input.fill('comparar resposta operacional');
    await page.keyboard.press('Enter');

    const assistantBubble = page.locator('.playground-message--assistant').last();
    await expect(assistantBubble).toBeVisible({ timeout: 10000 });
    await expect(assistantBubble).toContainText(
      /processando resposta|sem resposta retornada|falha de conexão|modo degradado|playground|resumo executivo/i,
    );
  });
});

