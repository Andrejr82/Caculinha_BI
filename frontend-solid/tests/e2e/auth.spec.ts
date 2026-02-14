import { test, expect } from '@playwright/test';

test.describe('Auth Smoke', () => {
  test('Login page renders credential inputs', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await expect(page.locator('#email')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('#password')).toBeVisible({ timeout: 30000 });
  });

  test('Can submit credentials and reach dashboard', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.fill('#email', 'user@agentbi.com');
    await page.fill('#password', 'user123');
    await page.click('button[type=\"submit\"]');
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 30000 });
  });
});
