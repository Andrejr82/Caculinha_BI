import { test, expect } from './setup';

test.describe('Monitoramento BI', () => {
  test('não carrega o chunk do Plotly no load inicial do dashboard', async ({ authenticatedPage: page }) => {
    const requests: string[] = [];
    page.on('requestfinished', (request) => requests.push(request.url()));

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const plotlyRequests = requests.filter((url) => /plotly-(core|trace-[a-z]+)/i.test(url));
    expect(plotlyRequests).toEqual([]);
  });

  test('carrega o dashboard, aplica filtros e abre drilldown sem overflow horizontal', async ({ authenticatedPage: page }) => {
    test.setTimeout(120000);

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: /monitoramento bi híbrido/i })).toBeVisible();
    await expect(page.getByTestId('dashboard-kpis')).toBeVisible();

    const hasHorizontalOverflow = await page.evaluate(() => {
      const main = document.querySelector('main');
      if (!main) return true;
      return main.scrollWidth > main.clientWidth;
    });
    expect(hasHorizontalOverflow).toBe(false);

    const segmentFilter = page.getByTestId('dashboard-segment-filter');
    const uneFilter = page.getByTestId('dashboard-une-filter');
    const clearFilters = page.getByTestId('dashboard-clear-filters');

    await expect(segmentFilter).toBeVisible();
    await expect(uneFilter).toBeVisible();

    await expect.poll(async () => segmentFilter.locator('option').count()).toBeGreaterThan(1);
    const segmentOptions = await segmentFilter.locator('option').evaluateAll((options) =>
      options.map((option) => ({ value: (option as HTMLOptionElement).value, label: option.textContent?.trim() || '' })),
    );
    const firstSegment = segmentOptions.find((option) => option.value);
    expect(firstSegment).toBeTruthy();

    await segmentFilter.selectOption(firstSegment!.value);
    await expect(page.locator('body')).toContainText(firstSegment!.label, { timeout: 30000 });

    await expect.poll(async () => uneFilter.locator('option').count()).toBeGreaterThan(1);
    const uneOptions = await uneFilter.locator('option').evaluateAll((options) =>
      options.map((option) => ({ value: (option as HTMLOptionElement).value, label: option.textContent?.trim() || '' })),
    );
    const firstUne = uneOptions.find((option) => option.value);
    expect(firstUne).toBeTruthy();

    await uneFilter.selectOption(firstUne!.value);
    await expect(page.locator('body')).toContainText(new RegExp(`UNE\\s+${firstUne!.value}`), { timeout: 30000 });

    await clearFilters.click();
    await expect(page.getByTestId('dashboard-segment-filter')).toHaveValue('');
    await expect(page.getByTestId('dashboard-une-filter')).toHaveValue('');
    await expect(page.locator('body')).toContainText('Rede completa', { timeout: 30000 });

    await page.getByRole('button', { name: /abrir rupturas/i }).click();
    await page.waitForURL(/\/rupturas(?:\?|$)/, { timeout: 30000 });
  });
});
