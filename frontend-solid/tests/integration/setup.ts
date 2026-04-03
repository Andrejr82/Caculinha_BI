import { test as base, expect, Page } from '@playwright/test';

/**
 * Setup e Fixtures para testes E2E
 * Agent Solution BI - Lojas Caçula
 */

export interface TestFixtures {
    authenticatedPage: Page;
    adminPage: Page;
}

/**
 * Credenciais de teste
 * IMPORTANTE: Usar credenciais de teste, não produção
 */
const TEST_USER = {
    email: 'user@agentbi.com',
    password: 'user123'
};

const TEST_ADMIN = {
    email: 'user@agentbi.com',
    password: 'user123'
};

/**
 * Função auxiliar para fazer login
 */
async function login(page: Page, email: string, password: string) {
    const emailInput = page.locator('#email, input[aria-label="Email"]').first();
    const passwordInput = page.locator('#password, input[aria-label="Senha"]').first();
    const submitButton = page.getByRole('button', { name: /entrar no sistema|entrar/i }).first();

    await page.goto('/login', { waitUntil: 'domcontentloaded' });

    try {
        await emailInput.waitFor({ state: 'visible', timeout: 30000 });
    } catch {
        // O dev server pode servir uma página em branco no primeiro hit enquanto recompila.
        await page.reload({ waitUntil: 'domcontentloaded' });
        await emailInput.waitFor({ state: 'visible', timeout: 30000 });
    }

    await passwordInput.waitFor({ state: 'visible', timeout: 30000 });

    // Preencher credenciais
    await emailInput.fill(email);
    await passwordInput.fill(password);

    // Submeter formulário
    await submitButton.click();

    // Aguardar redirecionamento
    await page.waitForURL('**/dashboard', { timeout: 30000 });
}

/**
 * Test com fixtures personalizadas
 */
export const test = base.extend<TestFixtures>({
    // Fixture para usuário comum autenticado
    authenticatedPage: async ({ page }, use) => {
        await login(page, TEST_USER.email, TEST_USER.password);
        await use(page);
    },

    // Fixture para admin autenticado
    adminPage: async ({ page }, use) => {
        await login(page, TEST_ADMIN.email, TEST_ADMIN.password);
        await use(page);
    }
});

export { expect };
