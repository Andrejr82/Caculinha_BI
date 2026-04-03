import { test, expect } from './setup';

test.describe('Chat UI Clean', () => {
  test('chat stays clean and new conversation resets the session', async ({ authenticatedPage: page }) => {
    await page.evaluate(() => localStorage.removeItem('chat_session_id'));
    await page.goto('/chat');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByRole('button', { name: 'Guias' })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Cesta' })).toHaveCount(0);

    const initialSessionId = await page.evaluate(() => localStorage.getItem('chat_session_id'));

    const chatInput = page.locator('textarea').first();
    await expect(chatInput).toBeVisible();
    await chatInput.fill('Teste rápido da nova conversa.');
    await chatInput.press('Enter');

    await expect(page.getByText('Teste rápido da nova conversa.')).toBeVisible({ timeout: 10000 });

    await page.getByRole('button', { name: 'Nova' }).first().click();

    await expect(page.getByText('Olá! Sou o Caçulinha. Posso analisar vendas, estoque e tendências para você. Como posso ajudar hoje?')).toBeVisible();
    await expect(chatInput).toHaveValue('');

    const nextSessionId = await page.evaluate(() => localStorage.getItem('chat_session_id'));
    expect(nextSessionId).toBeTruthy();
    expect(nextSessionId).not.toBe(initialSessionId);
  });
});
