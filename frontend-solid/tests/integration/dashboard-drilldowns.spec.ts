import { test, expect } from './setup';

test.describe('Drilldowns do Monitoramento BI', () => {
  test('abre Rupturas com filtros da URL', async ({ authenticatedPage: page }) => {
    await page.goto('/rupturas?segmento=ARMARINHO%20E%20CONFEC%C3%87%C3%83O&une=1685');
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('rupturas-scope-pill')).toContainText('UNE 1685');
    await expect(page.getByTestId('rupturas-segment-filter')).toHaveValue('ARMARINHO E CONFECÇÃO');
    await expect(page.getByTestId('rupturas-une-filter')).toHaveValue('1685');
  });

  test('abre Forecasting e Suppliers com contexto de segmento e UNE', async ({ authenticatedPage: page }) => {
    await page.goto('/forecasting?segmento=ARMARINHO%20E%20CONFEC%C3%87%C3%83O&une=1685');
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('forecasting-scope-pill')).toContainText('UNE 1685');
    await expect(page.getByTestId('forecasting-segment-filter')).toHaveValue('ARMARINHO E CONFECÇÃO');
    await expect(page.getByTestId('forecasting-une-filter')).toHaveValue('1685');

    await page.goto('/suppliers?segmento=ARMARINHO%20E%20CONFEC%C3%87%C3%83O');
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('suppliers-scope-pill')).toContainText('ARMARINHO E CONFECÇÃO');
    await expect(page.getByTestId('suppliers-segment-filter')).toHaveValue('ARMARINHO E CONFECÇÃO');
  });

  test('Forecasting renderiza com Chart.js sem carregar chunks do Plotly', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    const requests: string[] = [];
    page.on('requestfinished', (request) => requests.push(request.url()));

    await page.goto('/forecasting?segmento=ARMARINHO%20E%20CONFEC%C3%87%C3%83O&une=1685');
    await page.waitForLoadState('networkidle');

    await expect.poll(async () => page.getByTestId('forecasting-product-item').count()).toBeGreaterThan(0);
    await page.getByTestId('forecasting-product-item').first().click();

    await expect(page.getByTestId('forecasting-chart-panel')).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId('forecasting-chart-canvas')).toBeVisible({ timeout: 60000 });

    const plotlyRequests = requests.filter((url) => /plotly-(core|trace-[a-z]+)/i.test(url));
    expect(plotlyRequests).toEqual([]);
  });

  test('abre Transfers com segmento e UNE sugerida', async ({ authenticatedPage: page }) => {
    await page.goto('/transfers?segmento=ARMARINHO%20E%20CONFEC%C3%87%C3%83O&une=1685');
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('transfers-scope-pill')).toContainText('origem sugerida UNE 1685');
    await expect(page.getByTestId('transfers-segment-filter')).toHaveValue('ARMARINHO E CONFECÇÃO');
  });
});
