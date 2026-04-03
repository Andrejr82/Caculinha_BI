import { test, expect } from './setup';

const MODE_EXPECTATIONS = [
  {
    title: 'Abastecimento',
    prompt: 'Monte uma SQL para ruptura por loja, categoria e periodo.',
  },
  {
    title: 'Mix de Produtos',
    prompt: 'Quero um roteiro para revisar mix por curva ABC e margem.',
  },
  {
    title: 'Promocao e Preco',
    prompt: 'Estruture uma analise de ROI para campanha por categoria.',
  },
  {
    title: 'Devolucao e Transferencia',
    prompt: 'Preciso de uma SQL para sugerir transferencia entre lojas com excesso e falta.',
  },
  {
    title: 'Sazonalidade',
    prompt: 'Sugira um roteiro para previsao semanal por loja e categoria.',
  },
  {
    title: 'OPCOM Rotinas',
    prompt: 'Monte um checklist diario de OPCOM com SLA e dono por etapa.',
  },
];

test.describe('Playground Operational Modes', () => {
  test('renders all modes, updates the active mode state, and opens the approval desk', async ({
    adminPage: page,
  }) => {
    const consoleErrors: string[] = [];
    const serverErrors: string[] = [];

    page.on('console', (message) => {
      if (message.type() === 'error') {
        consoleErrors.push(message.text());
      }
    });

    page.on('response', (response) => {
      if (response.url().includes('/api/') && response.status() >= 500) {
        serverErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    await page.goto('/playground');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('.playground-hero')).toBeVisible();
    await expect(page.locator('.playground-mode-card')).toHaveCount(MODE_EXPECTATIONS.length);

    const promptInput = page.locator('textarea[aria-label="Prompt operacional"]');
    const activeModeValue = page.locator('.playground-kpi').first().locator('.playground-kpi-value');

    for (const mode of MODE_EXPECTATIONS) {
      const card = page.locator('.playground-mode-card', { hasText: mode.title }).first();
      await card.click();

      await expect(card).toHaveAttribute('aria-pressed', 'true');
      await expect(promptInput).toHaveAttribute('placeholder', mode.prompt);
      await expect(activeModeValue).toHaveText(mode.title);
    }

    await page.locator('.playground-mode-card', { hasText: 'Promocao e Preco' }).first().click();
    await promptInput.fill('Crie uma consulta SQL para margem e giro antes e depois de promocao.');
    await page.keyboard.press('Enter');

    const assistantBubble = page.locator('.playground-message--assistant').last();
    await expect(assistantBubble).toBeVisible({ timeout: 10000 });
    await expect(assistantBubble).toContainText(
      /processando resposta|sem resposta retornada|falha de conexão|modo degradado|playground|resumo executivo|sql/i,
    );

    await assistantBubble.getByRole('button', { name: /Solicitar aprovacao/i }).click();

    const approvalPreview = page.locator('.playground-preview-card');
    await expect(approvalPreview).toBeVisible();
    await expect(approvalPreview).toContainText(/Pedido original/i);
    await expect(approvalPreview).toContainText(/Saida gerada/i);

    expect(serverErrors).toEqual([]);
    expect(consoleErrors.filter((message) => !/favicon/i.test(message))).toEqual([]);
  });
});
