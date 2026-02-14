import { test, expect } from './setup';

/**
 * Testes de Autenticação
 * Agent Solution BI - Lojas Caçula
 */

test.describe('Autenticação', () => {
    test('Login com credenciais válidas', async ({ page }) => {
        await page.goto('/login');

        // Aguardar formulário carregar ou já estar no dashboard
        try {
            await page.waitForSelector('#email', { timeout: 5000 });

            // Preencher formulário
            await page.fill('#email', 'user@agentbi.com');
            await page.fill('#password', 'user123');

            // Submeter
            await page.click('button[type="submit"]');
        } catch (e) {
            // Se não encontrou o seletor, talvez já tenha redirecionado (já logado)
            console.log("ℹ️ Formulário não encontrado, verificando se já está autenticado...");
        }

        // Deve redirecionar para dashboard (ou já estar lá)
        // Aumentado timeout para 30s devido ao delay de 500ms e processos do backend (Supabase)
        await expect(page).toHaveURL(/.*dashboard/, { timeout: 30000 });

        // Screenshot de sucesso
        await page.screenshot({
            path: 'test-results/screenshots/auth-login-success.png',
            fullPage: true
        });
    });

    test('Login com credenciais inválidas', async ({ page }) => {
        await page.goto('/login');

        // Aguardar formulário carregar
        await page.waitForSelector('#email', { timeout: 10000 });

        // Preencher com credenciais inválidas
        await page.fill('#email', 'invalido@test.com');
        await page.fill('#password', 'senhaerrada');

        // Submeter
        await page.click('button[type="submit"]');

        // Aguardar um pouco para ver se há erro
        await page.waitForTimeout(2000);

        // Deve permanecer na página de login ou mostrar erro
        const currentUrl = page.url();
        expect(currentUrl).toContain('login');

        await page.screenshot({
            path: 'test-results/screenshots/auth-login-failure.png'
        });
    });

    test('Logout funciona', async ({ authenticatedPage: page }) => {
        // Já está autenticado via fixture

        // Procurar botão de logout (pode estar em menu dropdown)
        const logoutButton = page.locator('button:has-text("Sair"), a:has-text("Sair")').first();

        if (await logoutButton.isVisible()) {
            await logoutButton.click();
        } else {
            // Tentar abrir menu de usuário primeiro
            const userMenu = page.locator('[data-testid="user-menu"], button:has-text("Perfil")').first();
            if (await userMenu.isVisible()) {
                await userMenu.click();
                await page.waitForTimeout(500);
                await page.locator('button:has-text("Sair"), a:has-text("Sair")').first().click();
            }
        }

        // Deve redirecionar para login
        await expect(page).toHaveURL(/.*login/, { timeout: 5000 });
    });

    test('Redirecionamento quando não autenticado', async ({ page }) => {
        // Tentar acessar dashboard sem autenticação
        await page.goto('/dashboard');

        // Deve redirecionar para login
        await expect(page).toHaveURL(/.*login/, { timeout: 5000 });
    });
});
