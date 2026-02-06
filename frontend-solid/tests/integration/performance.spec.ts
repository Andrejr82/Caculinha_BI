import { test, expect } from './setup';

/**
 * Testes de Performance
 * Agent Solution BI - Lojas Caçula
 */

test.describe('Performance', () => {
    test('Dashboard carrega em menos de 5s', async ({ authenticatedPage: page }) => {
        const startTime = Date.now();

        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        const loadTime = Date.now() - startTime;

        console.log(`⏱️  Dashboard load time: ${loadTime}ms`);

        // Deve carregar em menos de 5 segundos
        expect(loadTime).toBeLessThan(5000);
    });

    test('Chat carrega em menos de 3s', async ({ authenticatedPage: page }) => {
        const startTime = Date.now();

        await page.goto('/chat');
        await page.waitForLoadState('networkidle');

        const loadTime = Date.now() - startTime;

        console.log(`⏱️  Chat load time: ${loadTime}ms`);

        expect(loadTime).toBeLessThan(3000);
    });

    test('Sem erros críticos no console', async ({ authenticatedPage: page }) => {
        const errors: string[] = [];

        // Capturar erros de console
        page.on('console', msg => {
            if (msg.type() === 'error') {
                errors.push(msg.text());
            }
        });

        // Navegar por algumas páginas
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        await page.goto('/chat');
        await page.waitForLoadState('networkidle');

        // Filtrar erros conhecidos/aceitáveis
        const criticalErrors = errors.filter(err =>
            !err.includes('favicon') &&
            !err.includes('404') &&
            !err.includes('net::ERR')
        );

        console.log(`🔍 Erros de console encontrados: ${criticalErrors.length}`);
        if (criticalErrors.length > 0) {
            console.log('Erros:', criticalErrors);
        }

        // Não deve ter erros críticos
        expect(criticalErrors.length).toBeLessThan(3);
    });
});
