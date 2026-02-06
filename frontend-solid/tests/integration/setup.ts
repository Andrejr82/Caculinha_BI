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
    email: 'teste@cacularetail.com.br',
    password: 'Teste@123'
};

const TEST_ADMIN = {
    email: 'admin@cacularetail.com.br',
    password: 'Admin@123'
};

/**
 * Função auxiliar para fazer login
 */
async function login(page: Page, email: string, password: string) {
    await page.goto('/login');

    // Aguardar formulário de login (usando id correto)
    await page.waitForSelector('#username', { timeout: 10000 });

    // Preencher credenciais
    await page.fill('#username', email);
    await page.fill('#password', password);

    // Submeter formulário
    await page.click('button[type="submit"]');

    // Aguardar redirecionamento
    await page.waitForURL('**/dashboard', { timeout: 10000 });
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
