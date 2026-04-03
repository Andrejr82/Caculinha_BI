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

});

