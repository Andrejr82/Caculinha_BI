import { test, expect } from './setup';

/**
 * Testes de Páginas
 * Agent Solution BI - Lojas Caçula
 */

test.describe('Páginas - Usuário Comum', () => {
    test('Dashboard carrega corretamente', async ({ authenticatedPage: page }) => {
        await page.goto('/dashboard');

        // Aguardar carregamento
        await page.waitForLoadState('networkidle');

        // Verificar título ou elemento principal
        await expect(page.locator('h1, h2').first()).toBeVisible();

        // Screenshot
        await page.screenshot({
            path: 'test-results/screenshots/page-dashboard.png',
            fullPage: true
        });
    });

    test('Chat carrega', async ({ authenticatedPage: page }) => {
        await page.goto('/chat');
        await page.waitForLoadState('networkidle');

        // Verificar textarea de mensagem
        const messageInput = page.locator('textarea, input[type="text"]').first();
        await expect(messageInput).toBeVisible();

        await page.screenshot({
            path: 'test-results/screenshots/page-chat.png',
            fullPage: true
        });
    });

    test('Rupturas carrega', async ({ authenticatedPage: page }) => {
        await page.goto('/rupturas');
        await page.waitForLoadState('networkidle');

        // Aguardar um pouco para dados carregarem
        await page.waitForTimeout(2000);

        await page.screenshot({
            path: 'test-results/screenshots/page-rupturas.png',
            fullPage: true
        });
    });

    test('Transfers carrega', async ({ authenticatedPage: page }) => {
        await page.goto('/transfers');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
            path: 'test-results/screenshots/page-transfers.png',
            fullPage: true
        });
    });

    test('Profile carrega', async ({ authenticatedPage: page }) => {
        await page.goto('/profile');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
            path: 'test-results/screenshots/page-profile.png',
            fullPage: true
        });
    });

    test('Help carrega', async ({ authenticatedPage: page }) => {
        await page.goto('/help');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
            path: 'test-results/screenshots/page-help.png',
            fullPage: true
        });
    });

    test('About carrega', async ({ authenticatedPage: page }) => {
        await page.goto('/about');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
            path: 'test-results/screenshots/page-about.png',
            fullPage: true
        });
    });
});

test.describe('Páginas - Admin Only', () => {
    test('Metrics (Analytics) carrega para admin', async ({ adminPage: page }) => {
        await page.goto('/metrics');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
            path: 'test-results/screenshots/page-metrics-admin.png',
            fullPage: true
        });
    });

    test('Reports carrega para admin', async ({ adminPage: page }) => {
        await page.goto('/reports');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
            path: 'test-results/screenshots/page-reports-admin.png',
            fullPage: true
        });
    });

    test('Admin carrega para admin', async ({ adminPage: page }) => {
        await page.goto('/admin');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
            path: 'test-results/screenshots/page-admin.png',
            fullPage: true
        });
    });

    test('Diagnostics carrega para admin', async ({ adminPage: page }) => {
        await page.goto('/diagnostics');
        await page.waitForLoadState('networkidle');

        await page.screenshot({
            path: 'test-results/screenshots/page-diagnostics-admin.png',
            fullPage: true
        });
    });
});
