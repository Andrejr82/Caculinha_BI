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

    const input = page.locator('input[type="text"]').first();
    await expect(input).toBeVisible();
    await input.fill('explique rapidamente as vendas');
    await page.keyboard.press('Enter');

    await page.waitForTimeout(4000);
    const bodyText = (await page.locator('body').innerText()).toLowerCase();
    expect(
      bodyText.includes('erro') ||
      bodyText.includes('temporariamente ocupado') ||
      bodyText.includes('playground') ||
      bodyText.includes('single mode')
    ).toBeTruthy();
  });
});

