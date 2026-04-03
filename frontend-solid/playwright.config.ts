import { defineConfig, devices } from '@playwright/test';

const backendCommand =
  process.env.PLAYWRIGHT_BACKEND_COMMAND ||
  (process.platform === 'win32'
    ? '"backend\\.venv\\Scripts\\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000'
    : '.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000');

const frontendCommand =
  process.env.PLAYWRIGHT_FRONTEND_COMMAND || 'bun run dev -- --host 127.0.0.1 --port 3000';

/**
 * Configuração do Playwright para testes E2E
 * Agent Solution BI - Lojas Caçula
 */
export default defineConfig({
    testDir: './tests',

    // Execução sequencial para evitar conflitos de estado
    fullyParallel: false,

    // Não permitir .only em CI
    forbidOnly: !!process.env.CI,

    // Retry em CI
    retries: process.env.CI ? 2 : 0,

    // 1 worker para execução sequencial
    workers: 1,

    // O setup autenticado pode consumir boa parte do orçamento em dev/HMR.
    timeout: 120 * 1000,
    outputDir: 'test-results/artifacts',

    // Reporters
    reporter: [
        ['html', { outputFolder: 'playwright-report', open: 'never' }],
        ['json', { outputFile: 'test-results/results.json' }],
        ['list']
    ],

    // Configurações globais
    use: {
        baseURL: 'http://localhost:3000',

        // Em ambiente local, reduzir pressão de memória.
        trace: process.env.CI ? 'on-first-retry' : 'off',

        // Screenshot apenas em falha
        screenshot: 'only-on-failure',

        // Vídeo apenas em CI para não sobrecarregar execuções locais.
        video: process.env.CI ? 'retain-on-failure' : 'off',

        // Timeout de navegação
        navigationTimeout: 30 * 1000,

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

    // Web Servers
    webServer: [
        {
            command: backendCommand,
            url: 'http://127.0.0.1:8000/health',
            cwd: '..',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
        },
        {
            command: frontendCommand,
            cwd: '.',
            url: 'http://localhost:3000',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
        },
    ],
});
