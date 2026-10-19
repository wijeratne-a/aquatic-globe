import { expect, test } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const shotsDir = path.join(__dirname, '../../artifacts/screenshots');

test('globe home and Atlantic cod heatmap', async ({ page }, testInfo) => {
  test.setTimeout(120_000);

  await page.goto('/');
  await page.waitForSelector('#cesium-container canvas', { timeout: 90_000 });
  await page.waitForTimeout(3000);

  const viewport = testInfo.project.name;
  await page.screenshot({
    path: path.join(shotsDir, `${viewport}-home.png`),
    fullPage: false,
  });

  const search = page.locator('#species-search');
  await search.click();
  await search.fill('Gadus morhua');
  const codResult = page.locator('#search-results li', { hasText: 'Atlantic cod' });
  await codResult.first().waitFor({ timeout: 15_000 });
  await codResult.first().click();

  await page.waitForSelector('#species-panel:not([hidden])', { timeout: 15_000 });
  await page.waitForTimeout(3500);
  await expect(page.locator('.illustrative-label')).toBeVisible();
  await expect(page.locator('#species-scientific')).toContainText(/Gadus morhua/i);

  await page.screenshot({
    path: path.join(shotsDir, `${viewport}-atlantic-cod.png`),
    fullPage: false,
  });
});
