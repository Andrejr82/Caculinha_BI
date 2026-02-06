import { defineConfig, devices } from '@playwright/test';

/**
 * Configuração do Playwright para testes E2E
 * Agent Solution BI - Lojas Caçula
 */
export default defineConfig({
    testDir: './tests/integration',

    // Execução sequencial para evitar conflitos de estado
    fullyParallel: false,

    // Não permitir .only em CI
    forbidOnly: !!process.env.CI,

    // Retry em CI
    retries: process.env.CI ? 2 : 0,

    // 1 worker para execução sequencial
    workers: 1,

    // Timeout de 30s por teste
    timeout: 30 * 1000,

    // Reporters
    reporter: [
        ['html', { outputFolder: 'test-results/html-report', open: 'never' }],
        ['json', { outputFile: 'test-results/results.json' }],
        ['list']
    ],

    // Configurações globais
    use: {
        baseURL: 'http://localhost:3000',

        // Trace apenas em retry
        trace: 'on-first-retry',

        // Screenshot apenas em falha
        screenshot: 'only-on-failure',

        // Vídeo apenas em falha
        video: 'retain-on-failure',

        // Timeout de navegação
        navigationTimeout: 10 * 1000,

        // Timeout de ação
        actionTimeout: 5 * 1000,
    },

    // Projetos (browsers)
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],

    // Web Server
    webServer: {
        command: 'npm run dev',
        url: 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
    },
});
